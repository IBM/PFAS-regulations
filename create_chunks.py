from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from llama_index.core import VectorStoreIndex, QueryBundle, Settings
from llama_index.core.schema import TextNode
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.nvidia import NVIDIAEmbedding
from transformers import AutoTokenizer
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
import sys
import numpy as np
import traceback
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

RITS_API_KEY = os.environ.get("RITS_API_KEY")

# ── Run flags ────────────────────────────────────────────────────────────────
# Set USE_ALL_MODELS = True to run the full model list instead of only granite4small.
USE_ALL_MODELS = False

# Set RUN_RAG = True to also run the RAG extraction loop over chunk_nums / embed_models.
RUN_RAG = False

# Set RUN_REFERENCE = True to extract and record the full reference text for each document.
RUN_REFERENCE = False
# ─────────────────────────────────────────────────────────────────────────────

PFAS_RELEVANCE_CRITERIA = """Evaluate if this text contains information that is relevant to a PFAS regulation.
If the text contains any of the following relevant information, return yes. If not, return no.
- location
- title
- type of regulation
- date of the overall document
- PFAS
- polyfluoroalkyl
- PFAS definition
- regulation related to PFAS
- penalties for noncompliance
- information describing the document type
- exceptions to the regulations
- products regulated
- testing requirements
- labeling requirements
- limits of chemicals
- places where PFAS needs to be tested
- reporting regulations
If there is regulation information but it is not related to PFAS, it is irrelevant. Information about penalties is irrelevant.
"""


def _build_text(chunks, headings):
    """Concatenate chunks, prepending a heading only when it changes."""
    text = ''
    for i, (chunk, heading) in enumerate(zip(chunks, headings)):
        if i == 0 or heading != headings[i - 1]:
            text += f'\n{heading}\n{chunk}'
        else:
            text += chunk
    return text


async def LLM_text(chunk_iter, model, smodel):
    """LLM Classifier strategy: prompt the model per chunk to assess PFAS relevance.

    Args:
        chunk_iter: Iterable of docling chunks.
        model: OpenAI client instance.
        smodel: Tuple of (model_id, short_name, base_url).

    Returns:
        Tuple of (total_length, condensed_text, condensed_length, error_count).
    """
    good_chunks, good_headings = [], []
    total_chunks, total_headings = [], []
    errors = 0

    for chunk in chunk_iter:
        total_chunks.append(chunk.text)
        head = chunk.meta.headings[0] if chunk.meta.headings is not None else ''
        total_headings.append(head)

        messages = [
            {
                'role': 'system',
                'content': 'You are a regulation expert to find information on PFAS regulations.'
            },
            {
                'role': 'user',
                'content': (
                    f'Here is a paragraph from a regulatory document:\n\n'
                    f'{head}\n{chunk.text}\n\n'
                    f'{PFAS_RELEVANCE_CRITERIA}'
                    f'Please do not return any discussion about evaluation.\n'
                    f'Return only yes or no. The answer should be either '
                    f'<answer>yes</answer> or <answer>no</answer>.'
                )
            },
        ]

        kwargs = dict(messages=messages, model=smodel[0], temperature=0)
        if 'gpt' not in smodel[1]:
            kwargs['max_tokens'] = 10
        completion = model.chat.completions.create(**kwargs)
        resp = completion.choices[0].message.content

        if 'yes' in resp.lower():
            good_chunks.append(chunk.text)
            good_headings.append(head)
        elif resp is not None and 'no' not in resp.lower():
            print('-----------------------------------------------------')
            print(f'LLM error — model: {smodel[1]}')
            print(f'Headings: {chunk.meta.headings}')
            print(f'Chunk: {chunk.text}')
            print(f'Response: {resp}')
            print('-----------------------------------------------------')
            errors += 1

    total_text = _build_text(total_chunks, total_headings)
    good_text = _build_text(good_chunks, good_headings)
    return len(total_text), good_text, len(good_text), errors


async def RAG_text(chunk_iter, chunk_num):
    """RAG Extraction strategy: embed chunks and retrieve top-N by similarity to the relevance prompt.

    Args:
        chunk_iter: Iterable of docling chunks.
        chunk_num: Number of top-k chunks to retrieve.

    Returns:
        Tuple of (total_length, condensed_text, condensed_length, error_or_None).
    """
    try:
        all_nodes = [
            TextNode(
                text=(chunk.meta.headings[0] + '\n' + chunk.text) if chunk.meta.headings is not None else chunk.text,
                id_=str(i)
            )
            for i, chunk in enumerate(chunk_iter)
        ]
        index = VectorStoreIndex(all_nodes)
        query_engine = index.as_retriever(similarity_top_k=chunk_num)
        nodes = query_engine._retrieve(QueryBundle(query_str=PFAS_RELEVANCE_CRITERIA))

        headings = [node.text.split('\n')[0] for node in nodes]
        texts = ['\n'.join(node.text.split('\n')[1:]) for node in nodes]
        order = np.argsort([int(node.node_id) for node in nodes])
        sorted_texts = [texts[i] for i in order]
        sorted_headings = [headings[i] for i in order]

        total_chunks = [chunk.text for chunk in chunk_iter]
        total_headings = [chunk.meta.headings[0] if chunk.meta.headings is not None else '' for chunk in chunk_iter]

        total_text = _build_text(total_chunks, total_headings)
        good_text = _build_text(sorted_texts, sorted_headings)
        return len(total_text), good_text, len(good_text), None

    except Exception:
        print('-----------------------------------------------------')
        print('RAG error')
        print(traceback.format_exc())
        print('-----------------------------------------------------')
        return 0, '', 0, traceback.format_exc()


async def run():
    chunk_sizes = [128, 256, 512, 1024]
    chunk_nums = [3, 10, 20, 50, 75]
    files = ["00", "06", "07", "09", "10", "12", "17", "18", "19", "20",
             "21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]

    single_model = [
        ("ibm-granite/granite-4.0-h-small", "granite4small",
         "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/granite-4-h-small/v1")
    ]
    all_models = [
        ("meta-llama/llama-4-maverick-17b-128e-instruct-fp8", "llama4",
         "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/llama-4-mvk-17b-128e-fp8/v1"),
        ("meta-llama/llama-3-3-70b-instruct", "llama3",
         "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/llama-3-3-70b-instruct/v1"),
        ("mistralai/mixtral-8x22B-instruct-v0.1", "mistral",
         "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/mixtral-8x22b-instruct-v01/v1"),
        ("ibm-granite/granite-3.3-8b-instruct", "granite3",
         "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/granite-3-3-8b-instruct/v1"),
        ("ibm-granite/granite-4.0-9b-prerelease-castlerock-r250626", "granite4",
         "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/granite-4-0-9b-castlerock/v1"),
        ("openai/gpt-oss-20b", "gpt20",
         "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/gpt-oss-20b/v1"),
        ("openai/gpt-oss-120b", "gpt120",
         "https://inference-3scale-apicast-production.apps.rits.fmaas.res.ibm.com/gpt-oss-120b/v1"),
    ]
    embed_models = [
        ("BAAI/bge-m3", "_baai"),
        ("intfloat/multilingual-e5-small", "_intfloat"),
        ("sentence-transformers/all-MiniLM-L6-v2", ""),
    ]

    models = all_models if USE_ALL_MODELS else single_model
    hf_tok = AutoTokenizer.from_pretrained("bert-base-uncased")
    result = json.load(open('./chunk_summary.json', 'r'))

    for file in files:
        print("\nDOCUMENT:", file)
        conv_res = DocumentConverter().convert(f"../../../data/Regulation/PDFs/document-{file}.pdf")

        # ── LLM Classifier ───────────────────────────────────────────────────
        for smodel in models:
            print(' - LLM text with model:', smodel[1])
            model = OpenAI(
                api_key=RITS_API_KEY,
                base_url=smodel[2],
                default_headers={'RITS_API_KEY': RITS_API_KEY}
            )
            for chunk_size in chunk_sizes:
                print('    chunk size:', chunk_size)
                chunker = HybridChunker(tokenizer=hf_tok, min_tokens=1, max_tokens=chunk_size,
                                        merge_peers=True, include_metadata=True)
                chunk_iter = chunker.chunk(dl_doc=conv_res.document)
                chunk_len, good_LLM_text, good_chunk_len, llm_error = await LLM_text(chunk_iter, model, smodel)
                LLM_name = f'{chunk_size}_LLM_{smodel[1]}_simple'
                with open(f'./outputs/{file}_{LLM_name}.txt', 'w') as f:
                    f.write(good_LLM_text)
                result[file][LLM_name] = {"cut_length": good_chunk_len, "full_length": chunk_len, "errors": llm_error}
                json.dump(result, open('./chunk_summary.json', 'w'))

        # ── RAG Extraction ───────────────────────────────────────────────────
        if RUN_RAG:
            for chunk_num in chunk_nums:
                print(' - RAG text with topk:', chunk_num)
                for chunk_size in chunk_sizes:
                    print('    chunk size:', chunk_size)
                    for embed_model in embed_models:
                        Settings.embed_model = HuggingFaceEmbedding(
                            model_name=embed_model[0], trust_remote_code=True
                        )
                        chunker = HybridChunker(tokenizer=hf_tok, min_tokens=1, max_tokens=chunk_size,
                                                merge_peers=True, include_metadata=True)
                        chunk_iter = chunker.chunk(dl_doc=conv_res.document)
                        doc_len, good_RAG_text, RAG_len, rag_error = await RAG_text(list(chunk_iter), chunk_num)
                        RAG_name = f'{chunk_size}_RAG_{embed_model[1]}_{chunk_num}_simple'
                        with open(f'./outputs/{file}_{RAG_name}.txt', 'w') as f:
                            f.write(good_RAG_text)
                        result[file][RAG_name] = {"cut_length": RAG_len, "full_length": doc_len, "errors": rag_error}
                        json.dump(result, open('./chunk_summary.json', 'w'))

        # ── Reference text extraction ─────────────────────────────────────────
        if RUN_REFERENCE:
            tokenizer = HuggingFaceTokenizer(
                tokenizer=AutoTokenizer.from_pretrained("bert-base-uncased"),
                max_tokens=50000
            )
            text = ' '.join([t.text for t in conv_res.document.texts])
            print('    reference token count:', tokenizer.count_tokens(text))
            result[file]['reference'] = {"cut_length": len(text), "full_length": len(text), "errors": None}
            json.dump(result, open('./chunk_summary.json', 'w'))


if __name__ == "__main__":
    asyncio.run(run())

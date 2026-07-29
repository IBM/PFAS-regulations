# PFAS-regulations

This repository contains the data which corresponds to the paper published.

## Repository Structure

### `golden_dataset_json/`
The ground-truth reference JSON files, one per document, used for evaluation.
Each file is named `document-NN.json` where `NN` is the document number.

### `golden_dataset_txts/`
Pre-processed plain-text versions of the regulatory documents used as input to the extraction scripts.
Each file is named `document-NN.txt` where `NN` is the document number.

### `text_chunks/`
Text files produced by applying the **docling chunker** to each document for various chunk sizes, tokenizers/models, and subsequent document condensation via the LLM Classifier or RAG Extraction strategies described below.
See [`text_chunks/README.md`](text_chunks/README.md) for the full naming convention.

### `output/`
Information extraction results produced by running IE prompts on the **full document** across multiple models and prompt strategies.

**Structure:** `output/{provider}/{model}/{prompt_strategy}/document-NN.json`

**Models:**
| Provider | Model |
|----------|-------|
| `ibm-granite` | `granite-3.3-8b-instruct`, `granite-4.0-h-micro` |
| `meta-llama` | `llama-3-3-70b-instruct`, `llama-4-maverick-17b-128e-instruct-fp8` |
| `mistralai` | `mixtral-8x22B-instruct-v0.1` |
| `openai` | `gpt-4o`, `gpt-oss-20b`, `gpt-oss-120b` |

**Prompt strategies:**
| Folder name | Description |
|-------------|-------------|
| `IE_prompt_data_seperation_strategy_seperated_prompting_regulation_max8192` | **Separated Prompting**: regulation-level fields extracted in an independent step |
| `IE_prompt_data_seperation_strategy_seperated_prompting_metadata_max8192` | **Separated Prompting**: metadata fields extracted in an independent step |
| `IE_prompt_prompting_style_NOToneshot_max8192` | **Zero-shot**: direct prompts without examples |
| `IE_prompt_prompting_style_few_shot_structured_max8192` | **Few-shot Structured**: prompts with a schema example and example values for each field |
| `IE_prompt_schema_design_joint_extraction_max8192` | **Joint Extraction**: field values and provenance spans extracted together in a single prompt |
| `IE_prompt_schema_design_sequential_extraction_values_max8192` | **Sequential Extraction (step 1)**: field values extracted first |
| `IE_prompt_schema_design_sequential_extraction_provenance_max8192` | **Sequential Extraction (step 2)**: provenance spans extracted separately based on predicted values |
| `sequential_single_field_max8192` | **Field-by-Field Prompting**: separate prompt issued for each individual metadata field |

Each prompt strategy folder contains one `document-NN.json` result file per document, plus a `processing_times.log` recording processing time per document.

### `output_LLM/`
Information extraction results produced using the **LLM Classifier** document condensation strategy: an LLM is prompted per chunk to assess relevance to PFAS regulations, and the selected chunks are concatenated into a condensed document which is then passed to the IE prompt pipeline. Only `gpt-4o` results are included.

**Structure:** `output_LLM/openai/gpt-4o/{prompt_strategy}/document-NN.json`

Prompt strategies are the same as described for `output/` above.

### `output_RAG/`
Information extraction results produced using the **RAG Extraction** document condensation strategy: each chunk is embedded and the top-N chunks by similarity to a reference prompt are retrieved and used as context for the IE prompt pipeline. Only `gpt-4o` results are included.

**Structure:** `output_RAG/openai/gpt-4o/{prompt_strategy}/document-NN.json`

Prompt strategies are the same as described for `output/` above.

## Scripts

> **Note:** All scripts have been modified slightly for this presentation of the data and are untested.

### [`create_chunks.py`](create_chunks.py)
Processes regulatory PDF documents through the docling `HybridChunker` and applies one or both of the document condensation strategies used to produce the files in `text_chunks/`:
- **LLM Classifier** — prompts an LLM per chunk to assess PFAS relevance; selected chunks are concatenated into a condensed document.
- **RAG Extraction** — embeds each chunk and retrieves the top-N most similar to a PFAS relevance prompt using a vector index.

Results and chunk statistics are saved to `chunk_summary.json`. Three flags at the top of the script (`USE_ALL_MODELS`, `RUN_RAG`, `RUN_REFERENCE`) control which models and strategies are run.

**Requires:** `RITS_API_KEY` environment variable.

### [`extract_regulation_info.py`](extract_regulation_info.py)
Runs a single-pass information extraction over all documents in `golden_dataset_txts/` using a chosen prompt and IBM watsonx.ai model. For each document it calls the LLM once, saves the raw API response, then post-processes all outputs via `extract_json_from_output.py` to produce clean `document-NN.json` files.

Run interactively — the script prompts for prompt name, model name, and `max_new_tokens`:

```bash
python extract_regulation_info.py
```

**Requires:** `WX_SERVICE_ID_API_KEY` and `WX_PROJECT_ID` environment variables (see `.env.example`).

### [`extract_regulation_pipeline.py`](extract_regulation_pipeline.py)
Extended extraction pipeline with support for a two-pass **sequential provenance extraction** mode:
- For standard prompt names it behaves like `extract_regulation_info.py`, writing results to `output_updated/`.
- For `IE_prompt_schema_design_sequential_extraction_provenance`, it reads the already-cleaned output from a prior `IE_prompt_schema_design_sequential_extraction_values` run, injects it into the prompt via `insert_prev_json`, and performs a second LLM pass to add provenance spans.

Run interactively — the script prompts for prompt name, model name, and `max_new_tokens`:

```bash
python extract_regulation_pipeline.py
```

**Requires:** `WX_SERVICE_ID_API_KEY` and `WX_PROJECT_ID` environment variables (see `.env.example`).

### [`extract_json_from_output.py`](extract_json_from_output.py)
Post-processing utility called automatically by the extraction scripts above. The raw watsonx.ai API response wraps the model output in `{"results": [{"generated_text": "..."}]}`; this script strips that wrapper, extracts the JSON object from `generated_text` using regex, and overwrites the source file with the cleaned JSON.

Can also be run standalone against a directory of raw output files:

```bash
python extract_json_from_output.py <output_dir>
```

### [`prompts.py`](prompts.py)
Defines all IE prompt templates and helper functions used by the extraction scripts:
- `IE_prompt_schema_design_joint_extraction` — joint extraction of field values and provenance in one prompt.
- `IE_prompt_schema_design_sequential_extraction_values` — step 1 of sequential extraction; extracts field values only.
- `IE_prompt_data_seperation_strategy_seperated_prompting_metadata` — separated prompting for metadata fields.
- `IE_prompt_data_seperation_strategy_seperated_prompting_regulation` — separated prompting for regulation-level fields.
- `IE_prompt_prompting_style_NOToneshot` — zero-shot prompt style.
- `IE_prompt_prompting_style_few_shot_structured` — few-shot structured prompt with schema and example values.
- `add_provenance(value_json)` — wraps a value JSON with provenance placeholders.
- `insert_prev_json(prov_json)` — inserts a prior extraction result into the sequential provenance prompt.

### [`evaluation.py`](evaluation.py)
Evaluates model output JSON files against the `golden_dataset_json/` ground truth, scoring each document across metadata and regulation-level fields using exact match, F1, and ROUGE-Lsum metrics. Results are written to a timestamped `.txt` file.

```bash
python evaluation.py <pred_folder> [--gt_folder golden_dataset_json] [--output results.txt]
```

## Setup

### Requirements

Install all dependencies with:

```bash
pip install -r requirements.txt
```

| Package | Used by |
|---------|---------|
| `ibm-watsonx-ai` | `extract_regulation_info.py`, `extract_regulation_pipeline.py` |
| `python-dotenv` | `extract_regulation_info.py`, `extract_regulation_pipeline.py` |
| `rouge-score` | `evaluation.py` |
| `docling` | `create_chunks.py` |
| `docling-core` | `create_chunks.py` |
| `llama-index-core` | `create_chunks.py` |
| `llama-index-embeddings-huggingface` | `create_chunks.py` |
| `llama-index-embeddings-nvidia` | `create_chunks.py` |
| `transformers` | `create_chunks.py` |
| `openai` | `create_chunks.py` |
| `numpy` | `create_chunks.py` |

### Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `WX_SERVICE_ID_API_KEY` | IBM watsonx.ai Service ID API key |
| `WX_PROJECT_ID` | IBM watsonx.ai project ID |

## License

If you would like to see the detailed LICENSE click [here](LICENSE).

```text
#
# Copyright IBM Corp. 2025
# SPDX-License-Identifier: Apache-2.0
#
```

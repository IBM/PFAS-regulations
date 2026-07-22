# PFAS-regulations

This repository contains the data which corresponds to the paper published.

## Repository Structure

### `golden_dataset/`
The ground-truth reference JSON files, one per document, used for evaluation.
Each file is named `document-NN.json` where `NN` is the document number.

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

## License

If you would like to see the detailed LICENSE click [here](LICENSE).

```text
#
# Copyright IBM Corp. 2025
# SPDX-License-Identifier: Apache-2.0
#
```

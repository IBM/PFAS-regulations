These are the information extraction results produced using **RAG-retrieved chunks** (from `text_chunks`) as context for the prompt pipeline. Only `gpt-4o` results are included.

**Structure:** `openai/gpt-4o/{prompt_strategy}/document-NN.json`

## Prompt Strategies

| Folder name | Description |
|-------------|-------------|
| `IE_prompt_data_seperation_strategy_seperated_prompting_regulation_max8192` | Data separation strategy: regulation fields prompted separately |
| `IE_prompt_data_seperation_strategy_seperated_prompting_metadata_max8192` | Data separation strategy: metadata fields prompted separately |
| `IE_prompt_prompting_style_NOToneshot_max8192` | Prompting style: zero-shot (no examples) |
| `IE_prompt_prompting_style_few_shot_structured_max8192` | Prompting style: few-shot with structured examples |
| `IE_prompt_schema_design_joint_extraction_max8192` | Schema design: all fields extracted jointly in one prompt |
| `IE_prompt_schema_design_sequential_extraction_values_max8192` | Schema design: fields extracted sequentially (values only) |
| `IE_prompt_schema_design_sequential_extraction_provenance_max8192` | Schema design: fields extracted sequentially (with provenance) |
| `sequential_single_field_max8192` | Single field extracted per prompt, sequentially |

Each prompt strategy folder contains one `document-NN.json` result file per document, plus a `processing_times.log` recording the processing time per document.

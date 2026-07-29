import os
import json
import time
import subprocess
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from dotenv import load_dotenv
from prompts import (
    IE_prompt_schema_design_joint_extraction,
    IE_prompt_schema_design_sequential_extraction_values,
    insert_prev_json,
    IE_prompt_data_seperation_strategy_seperated_prompting_metadata,
    IE_prompt_data_seperation_strategy_seperated_prompting_regulation,
    IE_prompt_prompting_style_NOToneshot,
    IE_prompt_prompting_style_few_shot_structured,
)

load_dotenv()

WX_SERVICE_ID_API_KEY = os.environ.get("WX_SERVICE_ID_API_KEY")
WX_PROJECT_ID = os.environ.get("WX_PROJECT_ID")
WX_URL = "https://us-south.ml.cloud.ibm.com"

PROMPT_MAP = {
    "IE_prompt_schema_design_joint_extraction": IE_prompt_schema_design_joint_extraction,
    "IE_prompt_schema_design_sequential_extraction_values": IE_prompt_schema_design_sequential_extraction_values,
    "IE_prompt_data_seperation_strategy_seperated_prompting_metadata": IE_prompt_data_seperation_strategy_seperated_prompting_metadata,
    "IE_prompt_data_seperation_strategy_seperated_prompting_regulation": IE_prompt_data_seperation_strategy_seperated_prompting_regulation,
    "IE_prompt_prompting_style_NOToneshot": IE_prompt_prompting_style_NOToneshot,
    "IE_prompt_prompting_style_few_shot_structured": IE_prompt_prompting_style_few_shot_structured,
}

def extract_info_from_document(document_text, prompt, model_name, max_new_tokens):
    credentials = Credentials(
        url=WX_URL,
        api_key=WX_SERVICE_ID_API_KEY,
    )
    client = APIClient(credentials)
    model = ModelInference(
        model_id=model_name,
        api_client=client,
        project_id=WX_PROJECT_ID,
        params={"max_new_tokens": max_new_tokens},
    )
    full_prompt = f"{prompt}\n\nDocument:\n{document_text}"
    response = model.generate(full_prompt)
    return response

if __name__ == "__main__":
    prompt_name = input("Enter the prompt to use: ").strip()
    if prompt_name not in PROMPT_MAP and prompt_name != "IE_prompt_schema_design_sequential_extraction_provenance":
        raise ValueError(f"Invalid prompt name: {prompt_name}")

    model_name = input("Enter the model name (e.g., meta-llama/llama-3-3-70b-instruct): ").strip()
    max_new_tokens = input("Enter max_new_tokens (e.g., 8192): ").strip()
    try:
        max_new_tokens = int(max_new_tokens)
    except ValueError:
        raise ValueError("max_new_tokens must be an integer.")

    if prompt_name == "IE_prompt_schema_design_sequential_extraction_provenance":
        # Use the directory for sequential extraction values
        base_dir = f"../../data/output_updated/{model_name}/IE_prompt_schema_design_sequential_extraction_values_max{max_new_tokens}"
        output_dir = f"../../data/output_updated/{model_name}/{prompt_name}_max{max_new_tokens}"
        os.makedirs(output_dir, exist_ok=True)

        txt_dir = "golden_dataset_txts"
        txt_files = [f for f in os.listdir(txt_dir) if f.endswith(".txt")]

        for txt_file in txt_files:
            txt_path = os.path.join(txt_dir, txt_file)
            prior_file = f"{os.path.splitext(txt_file)[0]}.json"
            combined_path = os.path.join(base_dir, prior_file)

            # Check if the corresponding prior extraction file exists
            if not os.path.exists(combined_path):
                print(f"Warning: No corresponding extraction file found for {txt_file}")
                continue

            # Read the document text
            with open(txt_path, "r") as f:
                document_text = f.read()

            # Read the prior extraction file
            with open(combined_path, "r") as f:
                prov_json = json.load(f)

            # Generate the prompt using insert_prev_json
            prompt = insert_prev_json(json.dumps(prov_json, indent=2))

            # Run the extraction
            print(f"Running provenance extraction for {txt_file}...")
            result = extract_info_from_document(document_text, prompt, model_name, max_new_tokens)

            # Save the result
            output_fname = f"{os.path.splitext(txt_file)[0]}_provenance.json"
            output_path = os.path.join(output_dir, output_fname)
            with open(output_path, "w") as out_f:
                json.dump(result, out_f, indent=2)
            print(f"Provenance extraction saved to {output_path}")
    else:
        # Handle other prompts
        prompt = PROMPT_MAP[prompt_name]
        txt_dir = "golden_dataset_txts"
        output_dir = f"../../data/output_updated/{model_name}/{prompt_name}_max{max_new_tokens}"
        os.makedirs(output_dir, exist_ok=True)

        log_file_path = os.path.join(output_dir, "processing_times.log")
        with open(log_file_path, "w") as log_file:
            log_file.write("Document Name, Processing Time (seconds)\n")  # Write header

        txt_files = [f for f in os.listdir(txt_dir) if f.endswith(".txt")]
        for fname in txt_files:
            txt_path = os.path.join(txt_dir, fname)
            with open(txt_path, "r") as f:
                document_text = f.read()
            print(f"Running extraction for {fname}...")

            start_time = time.time()

            result = extract_info_from_document(document_text, prompt, model_name, max_new_tokens)

            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"Extraction for {fname} took {elapsed_time:.2f} seconds.")

            # Save the result
            output_fname = f"{os.path.splitext(fname)[0]}.json"
            output_path = os.path.join(output_dir, output_fname)
            with open(output_path, "w") as out_f:
                json.dump(result, out_f, indent=2)
            print(f"Extraction saved to {output_path}")

            # Log the processing time
            with open(log_file_path, "a") as log_file:
                log_file.write(f"{fname}, {elapsed_time:.2f}\n")

    print("Cleaning JSON outputs...")
    subprocess.run(
        [
            "python",
            "extract_json_from_output.py",
            os.path.abspath(output_dir),
        ]
    )
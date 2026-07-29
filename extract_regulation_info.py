import os
import json
import time  # Import the time module
from ibm_watsonx_ai import APIClient, Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from dotenv import load_dotenv      
from prompts import IE_prompt_schema_design_joint_extraction, IE_prompt_schema_design_sequential_extraction_values, insert_prev_json, IE_prompt_data_seperation_strategy_seperated_prompting_metadata, IE_prompt_data_seperation_strategy_seperated_prompting_regulation, IE_prompt_prompting_style_NOToneshot, IE_prompt_prompting_style_few_shot_structured
import subprocess

load_dotenv()

WX_SERVICE_ID_API_KEY = os.environ.get("WX_SERVICE_ID_API_KEY")
WX_PROJECT_ID =  os.environ.get("WX_PROJECT_ID")

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
        params={"max_new_tokens": max_new_tokens}
    )
    full_prompt = f"{prompt}\n\nDocument:\n{document_text}"
    response = model.generate(full_prompt)
    return response

if __name__ == "__main__":
    prompt_name = input("Enter the prompt to use: ").strip()
    if prompt_name not in PROMPT_MAP:
        raise ValueError(f"Invalid prompt name: {prompt_name}")

    model_name = input("Enter the model name (e.g., meta-llama/llama-3-3-70b-instruct): ").strip()
    max_new_tokens = input("Enter max_new_tokens (e.g., 8192): ").strip()
    try:
        max_new_tokens = int(max_new_tokens)
    except ValueError:
        raise ValueError("max_new_tokens must be an integer.")

    prompt = PROMPT_MAP[prompt_name]
    txt_dir = "golden_dataset_txts"
    output_dir = f"../../data/output/{model_name}/{prompt_name}_max{max_new_tokens}"
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
        
        # Measure the start time
        start_time = time.time()
        
        result = extract_info_from_document(document_text, prompt, model_name, max_new_tokens)
        
        # Measure the end time
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
    subprocess.run([
        "python",
        "extract_json_from_output.py",
        os.path.abspath(output_dir)
    ])
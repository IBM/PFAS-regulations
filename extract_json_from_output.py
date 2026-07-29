import json
import re
import os
import sys

def extract_and_save_clean_json(input_path):
    with open(input_path, "r") as f:
        data = json.load(f)
    # Get the generated_text
    generated_text = data["results"][0]["generated_text"]
    # Extract the JSON block using regex (between ``` or { ... })
    match = re.search(r"\{[\s\S]*\}", generated_text)
    if not match:
        raise ValueError(f"No JSON object found in generated_text for {input_path}.")
    json_str = match.group(0)
    # Parse the JSON string
    clean_json = json.loads(json_str)
    # Prepare output path (overwrite the source file with cleaned content)
    output_path = input_path
    # Save the cleaned JSON
    with open(output_path, "w") as out_f:
        json.dump(clean_json, out_f, indent=2)
    print(f"Cleaned JSON saved to {output_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        input_dir = "../../data/Regulation/golden_txts"
    
    files = [f for f in os.listdir(input_dir) if f.endswith(".json")]
    for fname in files:
        input_path = os.path.join(input_dir, fname)
        try:
            extract_and_save_clean_json(input_path)
        except Exception as e:
            print(f"Failed to process {fname}: {e}")


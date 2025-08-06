import pandas as pd
import json
import csv

# Load the CSV file
csv_file_path = 'natural_commentary.csv'
data = pd.read_csv(csv_file_path)

# Define the template for the instruction prefix
instruction_prefix = (
    "Provide an insightful analysis of the position, explaining the strengths, weaknesses, "
    "and strategic considerations for both sides. Include reasoning about pawn structure, "
    "piece activity, king safety, space, tactics, why one side if any is under pressure, "
    "and potential plans for each side."
)

# Prepare the data for JSONL format
output_data = []
for _, row in data.iterrows():
    fen = row['Input']  # Column holding the FEN
    response = row['Output']  # Column holding the model's response
    
    instruction = f"{instruction_prefix} Here is the chess position described by the FEN: {fen}"
    output_data.append({
        "instruction": instruction,  # Keep as a separate field
        "input": fen,                # Keep as a separate field
        "response": response         # Keep as a separate field
    })

# Save the output as a JSONL file
output_file_path = 'natural_commentary.jsonl'
with open(output_file_path, 'w') as f:
    for entry in output_data:
        json.dump(entry, f)
        f.write('\n')

print(f"Converted dataset saved to {output_file_path}")


def csv_to_jsonl_literacy(input_csv, output_jsonl):
    """
    Converts a literacy CSV to JSONL format with 'instruction', 'input', and 'response' as separate fields,
    while removing unwanted prompts and fixing typos.
    """
    unwanted_prompt = "Given some set of chess moves, write the best possible move"
    replacement_prompt = "Sort the given list of partial FENs from earlier in the game to later."

    print(f"Processing literacy CSV: {input_csv} -> {output_jsonl}")
    row_count = 0
    valid_row_count = 0

    with open(input_csv, 'r', encoding='utf-8') as csv_file, \
         open(output_jsonl, 'w', encoding='utf-8') as jsonl_file:
        
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            row_count += 1

            # Skip rows with the unwanted prompt
            if row.get('task') == unwanted_prompt:
                continue

            # Fix the typo "incomplit" -> "incomplete"
            row['task'] = row['task'].replace("incomplit", "incomplete")

            # Replace flawed prompt if it starts with <s>[INST]
            if row['task'].startswith("<s>[INST]"):
                row['task'] = replacement_prompt

            # Ensure necessary fields are present
            if not all(field in row for field in ['task', 'input', 'expected_output']):
                print(f"Skipping row {row_count} due to missing fields.")
                continue

            # Construct the JSONL entry with separate fields
            jsonl_entry = {
                "instruction": row['task'],           # The "task" becomes the instruction
                "input": row['input'],                # The input field from the CSV
                "response": row['expected_output']    # The expected output field becomes the response
            }

            # Write the JSONL entry
            jsonl_file.write(json.dumps(jsonl_entry, ensure_ascii=False) + '\n')
            valid_row_count += 1

            if row_count % 500 == 0:
                print(f"  Processed {row_count} rows, {valid_row_count} valid rows written so far.")

    print(f"Finished processing literacy CSV: {valid_row_count} valid rows written to {output_jsonl}")

# Example usage with provided paths
LITERACY_TEST_CSV = "test.csv"  # Replace with your test CSV file
LITERACY_TRAIN_CSV = "train.csv"  # Replace with your train CSV file
LITERACY_TEST_JSONL = "literacy_test.jsonl"  # Desired test JSONL output file
LITERACY_TRAIN_JSONL = "literacy_train.jsonl"  # Desired train JSONL output file

# Process both test and train datasets
csv_to_jsonl_literacy(LITERACY_TEST_CSV, LITERACY_TEST_JSONL)
csv_to_jsonl_literacy(LITERACY_TRAIN_CSV, LITERACY_TRAIN_JSONL)

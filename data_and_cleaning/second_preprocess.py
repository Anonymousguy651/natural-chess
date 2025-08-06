import pandas as pd

def remove_problematic_rows(input_file, output_file):
    """
    Removes rows from the dataset where the 'Output' column contains any of the
    problematic notations: '[csl', '[cal', '[gsl', '[eval', or '→'.

    Args:
        input_file (str): Path to the input CSV file.
        output_file (str): Path to save the filtered CSV file.
    """
    # Load the dataset
    df = pd.read_csv(input_file)
    print(f"Initial row count: {len(df)}")

    # List of problematic substrings to search for
    problematic_notations = ['[%csl', '[%cal', '[%eval', '→']

    # Create a mask to detect rows containing any problematic notation
    mask = df['Output'].apply(lambda x: any(notation in str(x) for notation in problematic_notations))

    # Debug: Count how many rows are being removed
    print(f"Rows containing problematic notations: {mask.sum()}")

    # Keep only rows that do not contain problematic notations
    filtered_df = df[~mask].copy()

    # Save the filtered dataset
    filtered_df.to_csv(output_file, index=False, quoting=1)  # quoting=1 is csv.QUOTE_ALL
    print(f"Filtered dataset saved to {output_file}")
    print(f"Final row count: {len(filtered_df)}")

if __name__ == "__main__":
    INPUT_FILE = "preprocessed_lichess_data.csv"  # Replace with your input file path
    OUTPUT_FILE = "natural_commentary.csv"  # Replace with your desired output file path
    remove_problematic_rows(INPUT_FILE, OUTPUT_FILE)

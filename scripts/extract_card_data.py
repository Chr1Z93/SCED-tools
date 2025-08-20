import json
import pandas as pd

# Define the JSON file paths using the provided file names (ArkhamDB format)
JSON_FILE_1 = "blbe.json"
JSON_FILE_2 = "blbe_encounter.json"

# Define the output Excel file path
OUTPUT_EXCEL_FILE = "extracted_data.xlsx"

# Define the fields you are interested in
FIELDS = ["name", "subname", "text", "back_text", "traits", "flavor", "back_flavor"]


def extract_data_from_json(file_path, fields_to_extract):
    """Extracts specified fields from a JSON file and returns them as list of dictionaries."""
    extracted_records = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Assuming the JSON structure is a list of objects at the top level.
        # If the structure is different, this part might need adjustment.
        items_to_process = []
        if isinstance(data, list):
            items_to_process = data
        elif isinstance(data, dict):
            # If it's a dictionary, iterate over its values.
            # This assumes each value is an item (dictionary) or a list of items.
            for key, value in data.items():
                if isinstance(value, dict):
                    items_to_process.append(value)
                elif isinstance(value, list):
                    items_to_process.extend(value)
        else:
            print(
                f"Warning: Unexpected JSON structure in {file_path}. Expected list or dict."
            )
            return []

        for item in items_to_process:
            record = {}
            for field in fields_to_extract:
                # Use .get() to safely access fields, returning None if not found
                record[field] = item.get(field)
            extracted_records.append(record)

    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}. Check file format.")
    except Exception as e:
        print(f"An unexpected error occurred while processing {file_path}: {e}")

    return extracted_records


def main():
    """Main function to orchestrate reading JSON files and writing to Excel."""
    all_extracted_data = []

    # Process the first JSON file
    print(f"Processing {JSON_FILE_1}...")
    data_from_file1 = extract_data_from_json(JSON_FILE_1, FIELDS)
    all_extracted_data.extend(data_from_file1)
    print(f"Extracted {len(data_from_file1)} records from {JSON_FILE_1}.")

    # Process the second JSON file
    print(f"Processing {JSON_FILE_2}...")
    data_from_file2 = extract_data_from_json(JSON_FILE_2, FIELDS)
    all_extracted_data.extend(data_from_file2)
    print(f"Extracted {len(data_from_file2)} records from {JSON_FILE_2}.")

    if not all_extracted_data:
        print("No data extracted. Exiting.")
        return

    # Create a Pandas DataFrame from the extracted data
    df = pd.DataFrame(all_extracted_data)

    # Write the DataFrame to an Excel file
    try:
        df.to_excel(OUTPUT_EXCEL_FILE, index=False)
        print(f"\nSuccessfully written extracted data to {OUTPUT_EXCEL_FILE}")
        print(f"Total records written: {len(df)}")
    except Exception as e:
        print(f"Error writing to Excel file: {e}")


if __name__ == "__main__":
    main()

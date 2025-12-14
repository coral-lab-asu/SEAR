#!/usr/bin/env python3
# filepath: /home/mvyas7/SEAR/TempTab-Recasting/src/scripts/database/load_context.py
import argparse
import os
import sys
import csv
import json
from pymongo import MongoClient, UpdateOne
from tqdm import tqdm
from dotenv import load_dotenv

# Define the project root directory correctly, one time.
# This script is in src/scripts/database, so we go up three levels.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

def get_mongo_client():
    """Establishes a connection to the MongoDB database."""
    # Load environment variables from the correctly located .env file
    load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
    
    uri = os.getenv("MONGODB_URI")
    if not uri:
        print(f"FATAL ERROR: MONGODB_URI not found in your .env file.", file=sys.stderr)
        print(f"Looked for .env at: {os.path.join(PROJECT_ROOT, '.env')}", file=sys.stderr)
        sys.exit(1)
    print("Connecting to MongoDB...")
    return MongoClient(uri)

def format_table_to_string(table_data, dataset_name):
    """Converts a table's JSON object into a clean, pipe-separated string."""
    if not table_data or not isinstance(table_data, dict):
        return None
    try:
        # Different datasets may have different table formats
        if dataset_name in ["fetaqa", "finqa"]:
            headers = table_data.get("headers", [])
            # Find all keys that start with 'row', sort them numerically to maintain order
            row_keys = sorted([key for key in table_data if key.startswith("row")], key=lambda x: int(x[3:]))
            rows = [table_data[key] for key in row_keys]

            header_str = " | ".join(map(str, headers))
            rows_str = "\n".join([" | ".join(map(str, row)) for row in rows])
            
            return f"{header_str}\n{rows_str}"
        elif dataset_name in ["hitabs", "tatqa"]:
            # Format for hitabs/tatqa datasets
            # Modify this based on the actual format of these datasets
            if "columns" in table_data and "rows" in table_data:
                header_str = " | ".join(map(str, table_data["columns"]))
                rows_str = "\n".join([" | ".join(map(str, row)) for row in table_data["rows"]])
                return f"{header_str}\n{rows_str}"
        else:
            # Generic format - try to handle any JSON structure
            if isinstance(table_data, dict):
                # Try to extract headers and rows based on common patterns
                headers = table_data.get("headers", table_data.get("columns", []))
                rows = table_data.get("rows", [])
                
                if headers and rows:
                    header_str = " | ".join(map(str, headers))
                    rows_str = "\n".join([" | ".join(map(str, row)) for row in rows])
                    return f"{header_str}\n{rows_str}"
                else:
                    # If standard format not found, serialize the JSON as a fallback
                    return json.dumps(table_data, indent=2)
            else:
                return str(table_data)
                
    except (TypeError, KeyError) as e:
        print(f"Warning: Could not format table due to error: {e}", file=sys.stderr)
        return None

def load_data_to_mongo(dataset_name):
    """
    Reads dataset data and tables, then populates the context collection in MongoDB.
    """
    client = get_mongo_client()
    db = client[dataset_name]
    collection = db["context"]
    
    # Define paths to data files
    csv_file_path = os.path.join(PROJECT_ROOT, 'src', 'datasets', 'data', f'{dataset_name}.csv')
    json_tables_path = os.path.join(PROJECT_ROOT, 'src', 'datasets', 'tables', dataset_name, f'{dataset_name}.json')
    
    # Check if files exist
    if not os.path.exists(csv_file_path):
        print(f"FATAL ERROR: The dataset CSV file was not found at {csv_file_path}", file=sys.stderr)
        return False
        
    if not os.path.exists(json_tables_path):
        print(f"FATAL ERROR: The main table file was not found at {json_tables_path}", file=sys.stderr)
        return False

    # Load all table data into memory
    print(f"Loading all tables from {json_tables_path}...")
    try:
        with open(json_tables_path, 'r') as f:
            all_tables = json.load(f)
        print(f"Successfully loaded {len(all_tables)} tables into memory.")
        
        # Debug: Print sample table IDs for SQA dataset
        if dataset_name.lower() == "sqa":
            print("First 5 table IDs in SQA JSON file:")
            sample_keys = list(all_tables.keys())[:5]
            for key in sample_keys:
                print(f"- {key}")
            print(f"Total tables in JSON: {len(all_tables)}")
    except FileNotFoundError:
        print(f"FATAL ERROR: The main table file was not found at {json_tables_path}", file=sys.stderr)
        return False
    except json.JSONDecodeError:
        print(f"FATAL ERROR: Could not decode JSON from {json_tables_path}. Please check the file for errors.", file=sys.stderr)
        return False

    # Read CSV and prepare documents for MongoDB
    print(f"Reading questions from {csv_file_path} and preparing documents...")
    try:
        with open(csv_file_path, 'r') as f:
            csv_reader = list(csv.DictReader(f))
            if dataset_name.lower() == "sqa":
                print(f"SQA CSV header fields: {csv_reader[0].keys()}")
    except FileNotFoundError:
        print(f"FATAL ERROR: The dataset CSV file was not found at {csv_file_path}", file=sys.stderr)
        return False

    # Determine which field contains the table ID based on dataset
    table_id_field = {
        "fetaqa": "table_source_json",
        "finqa": "table_id",
        "hitabs": "table_id", 
        "hybridqa": "table_id",
        "multi": "table_id",
        "squall": "table_id",
        "tatqa": "table_id",
        "wiki": "table_id",
        "sqa": "table_id"
    }.get(dataset_name.lower(), "table_id")

    operations = []
    for i, row in enumerate(tqdm(csv_reader, desc=f"Processing {dataset_name} CSV rows")):
        table_id = row.get(table_id_field)
        if not table_id:
            if dataset_name.lower() == "finqa":
                # For FinQA, use Table_X format
                table_id = f"Table_{i+1}"
                print(f"Note: Using '{table_id}' as table_id for row {i+1}.")
            elif dataset_name.lower() == "sqa":
                # For SQA, we need to check if any field contains a reference to the table CSV file
                found = False
                
                # First, let's check if any field in the row contains something that looks like a table path
                for field, value in row.items():
                    if value and isinstance(value, str) and ('csv' in value.lower() or 'table' in value.lower()):
                        if value in all_tables:
                            table_id = value
                            print(f"Note: Found matching table ID '{table_id}' from field '{field}'.")
                            found = True
                            break
                
                if not found:
                    # Print all fields in this row to help identify where the table ID might be
                    print(f"Debug - Row {i+1} fields: {list(row.keys())}")
                    print(f"Debug - Row {i+1} values: {[row[k][:30] + '...' if isinstance(row[k], str) and len(row[k]) > 30 else row[k] for k in row.keys()]}")
                    
                    # Try to find table ID based on a pattern in the filename
                    # This is a placeholder - you would need to determine the actual pattern
                    print(f"Warning: Could not find a matching table ID for row {i+1}.")
                    continue
            else:
                print(f"Warning: Skipping row {i+1} due to missing '{table_id_field}'.", file=sys.stderr)
                continue

        table_content_json = all_tables.get(table_id)
        if not table_content_json:
            print(f"Warning: Skipping row {i+1}. Table ID '{table_id}' not found in the JSON file.", file=sys.stderr)
            continue
            
        formatted_table_body = format_table_to_string(table_content_json, dataset_name)
        if not formatted_table_body:
            print(f"Warning: Skipping row {i+1} because its table could not be formatted.", file=sys.stderr)
            continue

        # Build pretext based on dataset-specific fields
        pretext = ""
        # Different datasets may have different metadata fields
        if dataset_name == "fetaqa":
            section_text = row.get("table_section_text", "")
            page_title = row.get("table_page_title", "")
            section_title = row.get("table_section_title", "")
            
            if section_text: pretext += f'Relevant Section Text - {section_text}\n'
            if page_title: pretext += f'Table Title - {page_title}\n'
            if section_title: pretext += f'Table Subtitle - {section_title}\n'
        else:
            # Generic approach for other datasets - adapt as needed
            for key, value in row.items():
                if 'title' in key.lower() and value:
                    pretext += f'{key.replace("_", " ").title()} - {value}\n'
                    
        # Combine pretext and table body to match the desired format
        final_table_string = f'\n{pretext}{formatted_table_body}'

        # Create document with consistent field names across datasets
        document = {
            "q_num": i,
            "question": row.get("question", ""),
            "table": final_table_string,
            "table_id": table_id,
            "answer": row.get("answer", "")
        }
        
        operations.append(
            UpdateOne({"q_num": i}, {"$set": document}, upsert=True)
        )

    # Write to MongoDB
    if operations:
        print(f"\nWriting {len(operations)} documents to MongoDB via bulk operation...")
        try:
            result = collection.bulk_write(operations)
            print(f"Data population complete! Inserted: {result.upserted_count}, Modified: {result.modified_count}")
            return True
        except Exception as e:
            print(f"FATAL ERROR: An error occurred during the MongoDB bulk write: {e}", file=sys.stderr)
            return False
    else:
        print("No valid data was processed to be loaded into the database.")
        return False
        
    client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load dataset context into MongoDB.")
    parser.add_argument("--dataset", type=str, required=True, 
                        help="Dataset name to process (e.g., fetaqa, finqa, hitabs, etc.)")
    args = parser.parse_args()
    
    success = load_data_to_mongo(args.dataset)
    if success:
        print(f"Successfully loaded {args.dataset} context data into MongoDB.")
    else:
        print(f"Failed to load {args.dataset} context data into MongoDB.")
        sys.exit(1)
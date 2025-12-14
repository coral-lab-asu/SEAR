import os
import csv
import argparse
from pymongo import MongoClient, UpdateOne, ASCENDING
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

def get_client():
    load_dotenv()
    uri = os.getenv('MONGODB_URI')
    return MongoClient(uri, server_api=ServerApi('1'))

def get_column_mapping():
    #Rename this mapping to what you have in your CSV file
    #your_csv_column_name: 'mongo_field_name'
    return {
        'index': 'q_num',
        'question': 'question',
        'answer': 'answer',
        'response': 'response',
        'output': 'extracted_response',
        'code_output': 'code_output',
        'f1_score': 'f1_score_extracted_response',
        'f1_score_code_output': 'f1_score_code_output',
        'f1_final': 'f1_final',
        'GEM': 'gem_eval_extracted_response',
        'gem_eval_code_output': 'gem_eval_code_output',
        'GPT4': 'gpt_eval_extracted_response',
        'gpt_eval_code_output': 'gpt_eval_code_output',
        'gem_final': 'gem_final',
        'gpt4_final': 'gpt4_final',
        'eval_prompt': 'eval_prompt',
        'tag': 'tag',
        'notes': 'notes'
    }

def process_csv_file(file_path, db, reasoning_type, model):
    column_mapping = get_column_mapping()
    collection = db[reasoning_type]
    
    operations = []
    with open(file_path, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile)
        has_index = 'index' in csvreader.fieldnames

        for index, row in enumerate(csvreader):
            document = {'model': model, 'reasoning_type': reasoning_type}

            for column, mongo_field in column_mapping.items():
                if column == 'index':
                    if has_index:
                        document[mongo_field] = int(row[column]) if row[column] else None
                    else:
                        document[mongo_field] = index
                elif column in ['f1_score', 'f1_score_code_output', 'f1_final']:
                    try:
                        value = row.get(column, '')
                        if value and value.strip().lower() not in ['', 'null', 'none']:
                            document[mongo_field] = round(float(value), 3)
                        else:
                            document[mongo_field] = None
                    except ValueError:
                        document[mongo_field] = None
                else:
                    value = row.get(column, '')
                    if value and value.strip().lower() not in ['', 'null', 'none']:
                        document[mongo_field] = value
                    else:
                        document[mongo_field] = None
            
            operations.append(UpdateOne(
                {'q_num': document['q_num'], 'model': model, 'reasoning_type': reasoning_type},
                {'$set': document},
                upsert=True
            ))
    
    if operations:
        result = collection.bulk_write(operations)
        print(f"Upserted {result.upserted_count} and modified {result.modified_count} documents in {reasoning_type} collection")
    
    collection.create_index([('q_num', ASCENDING), ('model', ASCENDING)], name='q_num_model_index')
    print(f"Created composite index on q_num and model for {reasoning_type} collection")

def main(directory, dataset, model):
    client = get_client()
    if client is None:
        print("Failed to connect to MongoDB. Exiting.")
        return

    try:
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")

        db = client[dataset]
        
        for filename in os.listdir(directory):
            print(f"Processing file: {filename}")
            if filename.endswith('.csv'):
                reasoning_type = os.path.splitext(filename)[0].lower()
                file_path = os.path.join(directory, filename)
        
                process_csv_file(file_path, db, reasoning_type, model)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import CSV files to MongoDB")
    parser.add_argument("--directory", help="Directory containing CSV files")
    parser.add_argument("--dataset", help="Name of the dataset (will be used as database name)")
    parser.add_argument("--model", help="Name of the response model")
    args = parser.parse_args()

    main(args.directory, args.dataset, args.model)
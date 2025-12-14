import json
import yaml
import csv
import random
from ruamel.yaml import YAML
from io import StringIO
import pandas as pd

import argparse


def log_error(message):
    # You can expand this to log to a file or use logging frameworks
    print(message)


def get_table(path, table_id):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    table_data = None

    if path == "fetaqa":
        # Special case for fetaqa: all tables are in one large JSON file.
        file_path = os.path.join(project_root, 'src', 'datasets', 'tables', 'fetaqa', 'fetaqa.json')
        try:
            with open(file_path, "r") as file:
                all_tables = json.load(file)
            # The table_id is the key in this large JSON object.
            table_data = all_tables.get(table_id)
            if not table_data:
                log_error(f"Table ID '{table_id}' not found as a key in {file_path}")
                return None
        except FileNotFoundError:
            log_error(f"Consolidated table file not found: {file_path}")
            return None
        except json.JSONDecodeError:
            log_error(f"Error decoding JSON from {file_path}")
            return None
    else:
        # Original logic for datasets with individual table files.
        file_path = os.path.join(project_root, 'src', 'datasets', 'tables', path, table_id)
        try:
            with open(file_path, "r") as file:
                data = json.load(file)
                table_data = data.get(table_id, data)
        except FileNotFoundError:
            log_error(f"Individual table file not found: {file_path}")
            return None

    # --- Common Formatting Logic ---
    if not table_data or not isinstance(table_data, dict):
        log_error(f"Invalid or empty table data for ID '{table_id}'")
        return None

    try:
        headers = table_data.get("headers", [])
        row_keys = sorted([key for key in table_data if key.startswith("row")], key=lambda x: int(x[3:]))
        rows = [table_data[key] for key in row_keys]

        formatted_table = " | ".join(map(str, headers)) + "\n"
        formatted_table += "\n".join([" | ".join(map(str, row)) for row in rows])
        return formatted_table
    except (TypeError, KeyError) as e:
        log_error(f"Error formatting table data for ID '{table_id}': {e}")
        return None


def get_table_from_csv(file_path):

    try:
        with open(file_path, "r") as file:

            reader = csv.reader(file)
            headers = next(reader)[1:]
            formatted_table = " | ".join(headers) + "\n"
            rows = [" | ".join(row[1:]) for row in reader]
            formatted_table += "\n".join(rows)

    except FileNotFoundError:
        log_error(f"CSV file not found: {file_path}")
        return None

    return formatted_table


def clean_dict_keys(dict_data, df):

    new_dict = {}

    for key, value in dict_data.items():

        clean_key = key.replace("/wiki/", "").replace("_", " ")
        matched = False

        for cell in df.values.flatten():

            if clean_key.lower() in str(cell).lower():

                new_dict[str(cell)] = value
                matched = True
                break

        if not matched:
            new_dict[clean_key] = value

    return new_dict


def process_files(csv_path, json_path):

    try:
        df = pd.read_csv(csv_path)

    except FileNotFoundError:
        log_error(f"CSV file not found: {csv_path}")

        return

    try:
        with open(json_path, "r") as file:
            dictionary = json.load(file)

    except FileNotFoundError:
        log_error(f"JSON file not found: {json_path}")
        return

    cleaned_dictionary = clean_dict_keys(dictionary, df)
    with open(json_path, "w") as file:
        json.dump(cleaned_dictionary, file, indent=4)


def build_prompt2(path, r_type, context, question, **kwargs):

    meta = kwargs.get("meta", False)

    if meta:
        r_type = "meta_prompt"
        path = f"../../prompts/meta.yaml"
    else:
        path = f"../../prompts/{path}.yaml"

    try:
        with open(path, "r") as file:
            yaml_template = file.read()

    except FileNotFoundError:
        log_error(f"YAML file not found: {path}")
        return None

    yaml_str = yaml_template.format(
        context=context.replace("\n", "\n    "), question=question
    )
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml_data = yaml.load(yaml_str)
    output = StringIO()
    yaml.dump(yaml_data[r_type], output)
    full_yaml_str = output.getvalue()

    return full_yaml_str


def build_prompt3(path, r_type, context, question, **kwargs):
    meta = kwargs.get("meta", False)

    if meta:
        path = f"../../prompts/meta.yaml"
    else:
        path = f"../../prompts/{path}.yaml"

    try:
        with open(path, "r") as file:
            # Read the entire text file content
            text_template = file.read()
    except FileNotFoundError:
        log_error(f"Text file not found: {path}")
        return None

    formatted_text = text_template.format(context=context, question=question)

    return formatted_text


def build_prompt4(path, r_type, context, question, **kwargs):
    meta = kwargs.get("meta", False)

    if r_type == "meta":
        path = f"../../prompts/{path}.txt"

        try:
            with open(path, "r") as file:
                text_template = file.read()

            formatted_text = text_template.format(context=context, question=question)
            return formatted_text

        except FileNotFoundError:
            log_error(f"Text file not found: {path}")
            return None

    else:
        path = f"../../prompts/{path}.yaml"

    try:
        with open(path, "r") as file:
            yaml_template = file.read()
    except FileNotFoundError:
        log_error(f"YAML file not found: {path}")
        return None

    def format_context(text):
        return "\n".join(f"    {line}" for line in text.split("\n"))

    try:
        # Load the YAML template
        ruamel_yaml = YAML()
        yaml_data = ruamel_yaml.load(yaml_template)

        # Ensure the r_type key exists in the loaded YAML data
        if r_type not in yaml_data:
            yaml_data[r_type] = {}

        # Directly set context and question in the YAML structure
        yaml_data[r_type]["context"] = format_context(context)
        yaml_data[r_type]["question"] = question

        # Dump the updated YAML data to a string
        output = StringIO()
        ruamel_yaml.dump(yaml_data, output)
        full_yaml_str = output.getvalue()

        return full_yaml_str

    except Exception as e:
        log_error(f"Error processing YAML: {e}")
        print(f"Problematic YAML string:\n{yaml_data}")
        return None


def get_table_id(dataset, index, row):

    if dataset == "finqa":
        return f"Table_{index + 1}"

    elif dataset == "sqa":
        return row["table_file"]

    elif dataset == "fetaqa":
        return row["table_source_json"]

    elif dataset == "hybridqa":
        return row["table_id"]

    return None


from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne, ASCENDING
from pymongo.server_api import ServerApi
import os


def get_client():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    return MongoClient(uri, server_api=ServerApi("1"))


def get_prompts(dataset, reasoning, **kwargs):
    """
    Generator function to get prompts from a dataset.
    """
    # Define the base path of the project
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    
    # Construct the correct, absolute path to the data file
    file_path = os.path.join(project_root, 'src', 'datasets', 'data', f'{dataset}.csv')

    random = kwargs.get("random", False)
    rows = kwargs.get("rows", 3)
    from_index = kwargs.get("from_index", 0)
    run_all = kwargs.get("run_all", False)
    at_index = kwargs.get("at_index", None)

    db_index = 0
    run_all = kwargs.get("run_all", False)

    client = get_client()
    db = client[dataset]
    collection = db["context"]

    try:
        with open(file_path, "r") as file:
            csv_reader = csv.DictReader(file)
            data = list(csv_reader)
    except FileNotFoundError:
        log_error(f"CSV file not found: {file_path}")
        return

    size = len(data)
    print(f"Total rows in dataset: {size}")

    if at_index is not None:
        data = data[at_index : at_index + 1]
    else:
        if not run_all:
            if random:
                data = random.sample(data, min(rows, size))
            else:
                data = data[:min(rows, size)]

    for row in data:
        index = data.index(row)
        table_id = get_table_id(dataset, index, row)
        table = None
        print(f"Processing table {table_id}...")

        try:
            if dataset == "hybridqa":
                table = get_table_from_csv(
                    f"../../datasets/tables/{dataset}/tables/{table_id}.csv"
                )
            else:
                table = get_table(dataset, table_id)

        except FileNotFoundError:

            log_error(f"Table {table_id} not found in {dataset} dataset. Skipping...")
            continue

        if not table:
            continue

        if dataset == "fetaqa":
            # Safely get metadata from the row, providing an empty string as a default.
            section_text = row.get("table_section_text", "")
            page_title = row.get("table_page_title", "")
            section_title = row.get("table_section_title", "")

            # Build the pretext only with the metadata that actually exists.
            pretext = ""
            if section_text:
                pretext += f'Relevant Section Text - {section_text}\n'
            if page_title:
                pretext += f'Table Title - {page_title}\n'
            if section_title:
                pretext += f'Table Subtitle - {section_title}\n'
            
            table = f'\n{pretext}{table}'

        elif dataset == "finqa":
            table = f'\nTable Pretext - {row["pre_text"]}\nTable - \n{table}'

        elif dataset == "hybridqa":

            individual_file_path = (
                f"../../datasets/tables/{dataset}/tables/{table_id}.csv"
            )
            json_path = f"../../datasets/tables/{dataset}/request_tok/{table_id}.json"

            process_files(individual_file_path, json_path)

            try:
                with open(json_path, "r") as file:
                    data = json.load(file)
                table += f"\nMore context: \n\n{json.dumps(data, indent=4)}"

            except FileNotFoundError:
                log_error(f"File not found: {json_path}")
                continue

        prompt = build_prompt4(
            f"{dataset}/{reasoning.lower()}",
            reasoning,
            table,
            row["question"],
            **kwargs,
        )
        # prompt = PROMPT.format(context=table, question=row['question'])
        document = {
            "question": row["question"],
            "table": table,
            "table_id": table_id,
            "answer": row["answer"],
        }

        # print(prompt)

        if prompt:

            try:

                collection.update_one(
                    {"q_num": db_index}, {"$set": document}, upsert=True
                )

                db_index += 1

            except Exception as e:
                log_error(f"Error updating MongoDB: {e}")
                continue

            yield table_id, prompt, row["answer"], row["question"]


def create_batch_file(dataset, reasoning):
    path = f"../../datasets/data/{dataset}.csv"
    tasks = []
    index = 0

    for _, prompt, _, _ in get_prompts(dataset, reasoning, run_all=True):
        task = {
            "custom_id": f"{index}",
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an AI agent answering questions about a table. Please provide the answer to the question by referring to the table.",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        }
        index += 1
        tasks.append(task)

    file_name = f"./gpt4/data/prompts/{dataset}/{reasoning}.jsonl"
    with open(file_name, "w+") as file:
        for obj in tasks:
            file.write(json.dumps(obj) + "\n")


def append_response_to_file(index, table_id, question, response, answer, file_path):
    data = {
        "index": [index],
        "table_id": [table_id],
        "question": question,
        "response": [response],
        "answer": [answer],
    }

    df = pd.DataFrame(data)
    try:
        with open(file_path, "x") as file:
            df.to_csv(file, index=False)
    except FileExistsError:
        df.to_csv(file_path, mode="a", header=False, index=False)

    # print(f"Data appended to {file_path}")


def get_data_from_mongodb(
    client, dataset, sample_size=None, random_sample=False, **kwargs
):
    db = client[dataset]
    collection = db["context"]

    query = {}
    if "from_index" in kwargs:
        query["q_num"] = {"$gte": kwargs["from_index"]}

    if random_sample:
        data = list(collection.find(query))
        if sample_size and sample_size < len(data):
            return random.sample(data, sample_size)
        return data

    if sample_size:
        return list(collection.find(query).limit(sample_size))

    data = list(collection.find(query))
    print("Length of data", len(data))
    return data


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Generate prompts with meta template")
    parser.add_argument("--dataset", type=str, help="Dataset name")
    parser.add_argument("--reasoning", type=str, help="Reasoning type")
    parser.add_argument(
        "--rows", type=int, default=3, help="Number of rows to generate"
    )
    parser.add_argument(
        "--random", type=bool, default=False, help="Generate random rows"
    )
    parser.add_argument(
        "--meta", type=bool, default=False, help="Generate meta prompts"
    )
    parser.add_argument("--from_index", type=int, default=0, help="Start from index")
    parser.add_argument(
        "--at_index", type=int, default=0, help="Generate prompts at a specific index"
    )

    args = parser.parse_args()

    for _, prompt, _, _ in get_prompts(
        dataset=args.dataset, random=True, reasoning=args.reasoning, rows=args.rows
    ):
        print(prompt)

    # reasoning = ['COT', 'POT', 'Evidence', 'Faithful', 'Decomposition', 'meta']

    # for reason in reasoning:
    #     create_batch_file(args.dataset, reason)

import os
import yaml
from pymongo import MongoClient
from dotenv import load_dotenv
import argparse
from tqdm import tqdm

is_meta_enabled = False


def get_mongodb_client():
    load_dotenv()
    if is_meta_enabled:
        uri = os.getenv("MONGODB_URI_META")
    else:
        uri = os.getenv("MONGODB_URI_BASELINE")
    return MongoClient(uri)


def read_file_content(file_path):
    file_name = os.path.basename(file_path)
    _, file_extension = os.path.splitext(file_path)
    print(f"Reading file: {file_name} with extension: {file_extension}")

    if file_extension.lower() in [".yaml", ".yml"]:
        with open(file_path, "r") as file:
            try:
                # Try to load YAML and get the 'prompt' key
                return yaml.safe_load(file)["prompt"]
            except (yaml.YAMLError, TypeError, KeyError):
                # If it fails, reset pointer and read the whole file as text
                file.seek(0)
                return file.read()
    else:
        # For .txt and other files
        with open(file_path, "r") as file:
            return file.read()


def push_prompts(dataset, prompts_directory):
    client = get_mongodb_client()
    db = client[dataset]
    collection = db["prompts"]

    files = [
        f
        for f in os.listdir(prompts_directory)
        if f.endswith((".txt", ".yaml", ".yml"))
    ]

    for file_name in tqdm(files, desc="Uploading prompts"):
        file_path = os.path.join(prompts_directory, file_name)
        content = read_file_content(file_path)

        # Remove the file extension to get the reasoning
        reasoning = os.path.splitext(file_name)[0]

        prompt_doc = {"reasoning": reasoning, "content": content}

        collection.update_one(
            {"reasoning": reasoning}, {"$set": prompt_doc}, upsert=True
        )

    print(f"Uploaded {len(files)} prompts to the '{dataset}.prompts' collection.")
    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload prompts to MongoDB")
    parser.add_argument("--dataset", help="Name of the dataset (MongoDB database)")
    parser.add_argument("--directory", help="Directory containing prompt files")
    parser.add_argument(
        "--meta", action="store_true", help="Load the MongoDB data for meta experiments"
    )

    args = parser.parse_args()

    if args.meta:
        is_meta_enabled = True

    push_prompts(args.dataset, args.directory)

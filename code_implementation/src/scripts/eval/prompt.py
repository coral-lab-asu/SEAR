import os
import argparse
import json
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import traceback

SYS_PROMPT = """
You are an expert LLM evaluator tasked with assessing the accuracy of model responses against gold standard answers. Your role is to determine if the core content and intent of the model's response align with the gold answer, considering various answer formats and implicit information. Key guidelines:

Understand the question's essence, including specific operations or units mentioned.
Compare model responses to gold answers, focusing on key information.
Allow a small margin of error (±0.1%) for numerical answers.
Recognize correct answers in different formats (e.g., percentages, decimals).
Consider implicit information and context in responses.
For list-type answers, evaluate based on content rather than order. If more than 2 elements are missing (context-dependent), evaluate as incorrect.
Assess mathematical answers based on value range unless a specific value is required.
Check for appropriate units in mathematical answers.

Provide a "Yes" or "No" judgment without explanation unless requested.
"""

ALLOWED_REASONING_METHODS = {
    "cot",
    "pot",
    "decomposition",
    "faithful",
    "meta",
    "evidence",
    "clean_meta_3_step",
    "meta_3_step",
    "not",
    "tot",
    "got",
    "scp",
    "clear"
}


def get_client():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    return MongoClient(uri, server_api=ServerApi("1"))


def fetch_data(client, dataset, model, reasoning_methods, evaluator, sample, run_all):
    db = client[dataset]

    if evaluator.startswith("gpt"):
        evaluator = "gpt"
    elif evaluator.startswith("gemini"):
        evaluator = "gem"

    all_data = []
    total_count = 0

    for reasoning in reasoning_methods:
        if reasoning not in db.list_collection_names():
            print(f"Warning: Collection '{reasoning}' does not exist in the database.")
            continue

        collection = db[reasoning]

        base_query = {"model": model}

        if not run_all:
            base_query["$and"] = [
                {f"{evaluator}_eval_extracted_response": None},
                {f"{evaluator}_eval_code_output": None},
            ]

        print(f"Query for {reasoning}: {base_query}")

        collection_count = collection.count_documents(base_query)
        total_count += collection_count
        print(f"Documents to evaluate in {reasoning}: {collection_count}")

        pipeline = [
            {"$match": base_query},
            {
                "$project": {
                    "reasoning_type": 1,
                    "question": 1,
                    "answer": 1,
                    "response": 1,
                    "extracted_response": 1,
                    "code_output": 1,
                    "q_num": 1,
                }
            },
        ]

        if sample > 0:
            pipeline.append({"$sample": {"size": min(sample, collection_count)}})

        results = list(collection.aggregate(pipeline))

        for doc in results:
            doc["reasoning_type"] = reasoning

            if "q_num" not in doc:
                print(f"Warning: Document missing q_num: {doc}")
                doc["q_num"] = str(doc["_id"])

        all_data.extend(results)

    print(f"Total documents to evaluate: {total_count}")
    print(f"Documents after filtering and sampling: {len(all_data)}")

    return all_data, total_count


def construct_prompt(response_model, dataset, reasoning, sampled_data):
    with open("./prompt.txt", "r") as file:
        PROMPT = file.read()

    tasks = []
    tasks_co = []  # For meta code output

    for document in sampled_data:
        try:

            question = document["question"]
            answer = document["answer"]
            q_num = document["q_num"]

            if reasoning.lower() == "meta":
                response = document.get("response")
                code_output = document.get("code_output")

                if response:
                    prompt_er = PROMPT.format(
                        response=response, answer=answer, question=question
                    )
                    task_er = create_task(q_num, prompt_er)
                    tasks.append(task_er)

                if (
                    code_output
                    and code_output not in ["CODE ERROR", "ERROR"]
                    and "Error" not in code_output
                ):
                    prompt_co = PROMPT.format(
                        response=code_output, answer=answer, question=question
                    )
                    task_co = create_task(q_num, prompt_co)
                    tasks_co.append(task_co)

            elif reasoning.lower() in ["pot", "faithful"]:
                code_output = document.get("code_output", "")
                if (
                    code_output
                    and code_output not in ["CODE ERROR", "ERROR"]
                    and "Error" not in code_output
                ):
                    prompt = PROMPT.format(
                        response=code_output, answer=answer, question=question
                    )
                    task = create_task(q_num, prompt)
                    tasks.append(task)

            else:  # cot, decomposition, evidence
                response = document.get("response", "")
                if response:
                    prompt = PROMPT.format(
                        response=response, answer=answer, question=question
                    )
                    task = create_task(q_num, prompt)
                    tasks.append(task)
        except Exception as e:
            print(f"Error processing document: {e}")
            print(f"Problematic document: {document}")
            print(traceback.format_exc())

    save_tasks(response_model, dataset, reasoning, tasks)

    if reasoning.lower() == "meta" and tasks_co:
        save_tasks(response_model, dataset, "meta_co", tasks_co)


def create_task(q_num, prompt):
    return {
        "custom_id": f"{q_num}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYS_PROMPT},
                {"role": "user", "content": prompt},
            ],
        },
    }


def save_tasks(response_model, dataset, reasoning, tasks):
    os.makedirs(f"./prompts/{response_model}/{dataset}", exist_ok=True)
    file_name = f"./prompts/{response_model}/{dataset}/{reasoning}.jsonl"
    with open(file_name, "w") as file:
        for obj in tasks:
            file.write(json.dumps(obj) + "\n")
    print(f"Prompts for {reasoning} saved to {file_name}")


def update_empty_prompt_file(response_model, dataset, reasoning):
    os.makedirs(f"./prompts/{response_model}/{dataset}", exist_ok=True)
    file_name = f"./prompts/{response_model}/{dataset}/{reasoning}.jsonl"
    open(file_name, "w").close()
    print(f"Emptied prompt file for {reasoning}: {file_name}")


def clear_or_delete_prompt_files(response_model, dataset, reasoning_methods):
    for reasoning in reasoning_methods:
        file_path = f"./prompts/{response_model}/{dataset}/{reasoning}.jsonl"
        if os.path.exists(file_path):
            # Option 1: Clear the file
            open(file_path, "w").close()
            print(f"Cleared prompt file: {file_path}")

            # Option 2: Delete the file (uncomment if you prefer deletion)
            # os.remove(file_path)
            # print(f"Deleted prompt file: {file_path}")


def process_dataset(
    response_model, dataset, reasoning_methods, sample=0, evaluator="gpt", run_all=False
):
    client = get_client()
    if client is None:
        print("Failed to connect to MongoDB. Exiting.")
        return

    try:
        print(f"Connecting to dataset: {dataset}")
        print(f"Searching for model: {response_model}")
        print(f"Reasoning methods (collections): {reasoning_methods}")
        print(f"Evaluator: {evaluator}")
        print(f"Sample size: {sample}")
        print(f"Run all: {run_all}")

        data, total_count = fetch_data(
            client,
            dataset,
            response_model,
            reasoning_methods,
            evaluator,
            sample,
            run_all,
        )

        if not data:
            print("No documents found to evaluate. Clearing prompt files.")
            clear_or_delete_prompt_files(response_model, dataset, reasoning_methods)
            return

        grouped_data = {}
        for document in data:
            reasoning = document["reasoning_type"]
            if reasoning not in grouped_data:
                grouped_data[reasoning] = []
            grouped_data[reasoning].append(document)

        total_prompts = 0
        for reasoning in reasoning_methods:
            documents = grouped_data.get(reasoning, [])
            if documents:
                try:
                    construct_prompt(response_model, dataset, reasoning, documents)
                    total_prompts += len(documents)
                except Exception as e:
                    print(f"Error constructing prompts for {reasoning}: {e}")
                    print(traceback.format_exc())
            else:
                update_empty_prompt_file(response_model, dataset, reasoning)

        print(f"\nSummary:")
        print(f"Total documents to evaluate: {total_count}")
        print(f"Prompts built: {total_prompts}")
        print(f"Prompts per reasoning method:")
        for reasoning in reasoning_methods:
            print(f"  {reasoning}: {len(grouped_data.get(reasoning, []))}")

    except Exception as e:
        print(f"An error occurred: {e}")
        print(traceback.format_exc())
    finally:
        client.close()


def main():
    parser = argparse.ArgumentParser(description="Construct prompts for evaluation")
    parser.add_argument(
        "--response_model", type=str, required=True, help="Model response to evaluate"
    )
    parser.add_argument(
        "--dataset", type=str, required=True, help="Dataset name to verify"
    )
    parser.add_argument(
        "--reasoning",
        nargs="+",
        required=True,
        choices=[
            "pot",
            "imp_meta_3_step",
            "cot",
            "faithful",
            "decomposition",
            "meta_3_step",
            "meta",
            "evidence",
            "not",
            "tot",
            "got",
            "scp",
            "clear"
        ],
        help="Reasoning methods to process",
    )
    parser.add_argument(
        "--sample",
        default=0,
        type=int,
        help="Number of samples to evaluate (0 for all)",
    )
    parser.add_argument(
        "--evaluator",
        type=str,
        choices=["gpt", "gemini"],
        required=True,
        help="Evaluator to use",
    )
    parser.add_argument(
        "--run_all",
        action="store_true",
        help="Run for all documents regardless of evaluation status",
    )

    args = parser.parse_args()

    invalid_methods = set(args.reasoning) - ALLOWED_REASONING_METHODS
    if invalid_methods:
        print(f"Error: Invalid reasoning method(s): {', '.join(invalid_methods)}")
        print(f"Allowed methods are: {', '.join(ALLOWED_REASONING_METHODS)}")
        return

    if args.evaluator.startswith("gpt"):
        args.evaluator = "gpt"
    elif args.evaluator.startswith("gemini"):
        args.evaluator = "gem"

    process_dataset(
        args.response_model,
        args.dataset,
        args.reasoning,
        args.sample,
        args.evaluator,
        args.run_all,
    )


if __name__ == "__main__":
    main()

# Author - Abhishek Rajgaria
# Date - 27th Oct 2024
# Summary - Helper method for executing batch request

import os
import json
import time
from datetime import datetime, timedelta

from openai import OpenAI


def create_gpt_request(prompt, count, model, s1=False):
    """
    Method for creating the request structure for a single prompt.
    """
    req = {}

    messages = []

    message1 = {}
    message2 = {}
    message1["role"] = "system"
    message1["content"] = "You are a helpful assistant."
    if s1:
        message1["content"] = (
            "You are a meta-selector tasked with constructing the most efficient pathway for solving tabular questions."
        )

    message2["role"] = "user"
    message2["content"] = prompt

    messages.append(message1)
    messages.append(message2)

    body = {}
    # model = "gpt-3.5-turbo-0125"
    body["model"] = model
    body["messages"] = messages
    body["max_tokens"] = 1000

    id = "request-" + str(count)

    req["custom_id"] = id
    req["method"] = "POST"
    req["url"] = "/v1/chat/completions"
    req["body"] = body

    return req


def generate_request_jsonl(
    model_name, data, prompt, batch_request_file, step, question_details_dict=None
):
    """
    Generate Jsonl file where each line represent a request for each prompt.
    """

    cnt = 0
    question_id_to_request_id = {}
    try:

        jsonl_file = open(batch_request_file, "w")
        for doc in data:
            cnt += 1
            question = doc["question"]
            table = doc["table"]
            populated_prompt = ""
            request = {}
            if step == "s1":
                populated_prompt = prompt.format(table=table, question=question)

                request = create_gpt_request(populated_prompt, cnt, model_name, True)
            elif step == "s2":
                populated_prompt = prompt.format(
                    table=table,
                    question=question,
                    crucial_steps=question_details_dict[doc["q_num"]],
                )

                request = create_gpt_request(populated_prompt, cnt, model_name, False)

            else:
                populated_prompt = prompt.format(
                    table=table,
                    question=question,
                    detailed_steps=question_details_dict[doc["q_num"]],
                )

                request = create_gpt_request(populated_prompt, cnt, model_name, False)

            jsonl_file.write(json.dumps(request) + "\n")
            question_id_to_request_id[doc["q_num"]] = request["custom_id"]
            return question_id_to_request_id
    except:
        # Do nothing
        print("Error while creating json request, cnt ", cnt)
    finally:
        jsonl_file.close()


def send_batch_request(batch_request_file, client):
    batch_input_file = client.files.create(
        file=open(batch_request_file, "rb"), purpose="batch"
    )
    batch_input_file_id = batch_input_file.id

    return client.batches.create(
        input_file_id=batch_input_file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "nightly eval job"},
    )


def check_batch_status(client, batch_id):
    start_time = datetime.now()
    timeout = timedelta(hours=24)

    while datetime.now() - start_time < timeout:
        batch = client.batches.retrieve(batch_id)
        if batch.status == "completed":
            return batch
        elif batch.status in ["failed", "cancelled"]:
            raise Exception(f"Batch failed or was cancelled. Status: {batch.status}")
        time.sleep(30)  # Check every 30s

    raise TimeoutError("Batch processing timed out after 24 hours")


def retrieve(client, batch_job):
    try:
        batch = check_batch_status(client, batch_job.id)
    except TimeoutError as e:
        print(f"Error: {e}")
        print("Attempting to cancel the batch...")
        client.batches.cancel(batch_job.id)
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    print(batch)
    result_file_id = batch.output_file_id
    result_content = client.files.content(result_file_id).text
    return result_content


def get_question_to_response(question_request_dict, responses):
    lines = responses.strip().split("\n")
    request_content_dict = {}
    for line in lines:
        json_obj = json.loads(line.strip())
        request_id = json_obj["custom_id"]
        response_content = json_obj["response"]["body"]["choices"][0]["message"][
            "content"
        ]
        request_content_dict[request_id] = response_content

    question_response_dict = {}
    for q_num in question_request_dict.keys():
        question_response_dict[q_num] = request_content_dict[
            question_request_dict[q_num]
        ]

    return question_response_dict
#TODO update the folders
#TODO create your own steps for the prompts (Optional)

def perform_batch_request(
    model_name,
    dataset,
    data,
    prompts,
    reasoning,
    s1_model,
    s2_model,
    s3_model,
    table_type="normal_pipe",
):
    """
    Processing Batch request for Meta 3 steps prompting.
    """

    batch_request_filepath = (
        f"./gpt_three_step/requests/{model_name}/{dataset}/{reasoning}/{table_type}"
    )

    os.makedirs(batch_request_filepath, exist_ok=True)

    # Getting Crucial Steps

    batch_request_filepath_s1 = f"{batch_request_filepath}s1.jsonl"
    question_to_request_dict_s1 = generate_request_jsonl(
        model_name,
        data,
        prompts[0],
        batch_request_filepath_s1,
        "s1",
    )

    s1_batch_job = send_batch_request(batch_request_filepath_s1, s1_model)

    s1_responses = retrieve(s1_model, s1_batch_job)

    question_critical_steps = get_question_to_response(
        question_to_request_dict_s1, s1_responses
    )

    # Getting Detailed Steps

    batch_request_filepath_s2 = f"{batch_request_filepath}s2.jsonl"

    question_to_request_dict_s2 = generate_request_jsonl(
        model_name,
        data,
        prompts[1],
        batch_request_filepath_s2,
        "s2",
        question_critical_steps,
    )

    s2_batch_job = send_batch_request(batch_request_filepath_s2, s2_model)

    s2_responses = retrieve(s2_model, s2_batch_job)

    question_detailed_steps = get_question_to_response(
        question_to_request_dict_s2, s2_responses
    )

    # Getting Final Response

    batch_request_filepath_s3 = f"{batch_request_filepath}s3.jsonl"

    question_to_request_dict_s3 = generate_request_jsonl(
        model_name,
        data,
        prompts[2],
        batch_request_filepath_s3,
        "s3",
        question_detailed_steps,
    )

    s3_batch_job = send_batch_request(batch_request_filepath_s3, s3_model)

    s3_responses = retrieve(s3_model, s3_batch_job)

    question_final_response = get_question_to_response(
        question_to_request_dict_s3, s3_responses
    )

    # Combine crucial steps, detailed steps and final response -
    final_results = []

    for doc in data:
        obj = {
            "q_num": doc["q_num"],
            "reasoning": reasoning,
            "table_id": doc["table_id"],
            "question": doc["question"],
            "crucial_steps": question_critical_steps[doc["q_num"]],
            "detailed_steps": question_detailed_steps[doc["q_num"]],
            "response": question_final_response[doc["q_num"]],
            "answer": doc["answer"],
        }
        final_results.append(obj)

    return final_results

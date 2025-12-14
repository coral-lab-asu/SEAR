import google.generativeai as genai
import re
import os
import io
import contextlib
import signal
# from groq import Groq
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi


def palm_results(prompt, model):
    completion = genai.generate_text(
        model=model,
        prompt=prompt,
        safety_settings=None,
        max_output_tokens=1000,
        # The maximum length of the response
    )
    return completion.result


def get_client():
    load_dotenv()
    uri = os.getenv("MONGODB_URI")
    return MongoClient(uri, server_api=ServerApi("1"))


def gemini_response(prompt, model):
    response = model.generate_content(prompt)
    return response.text


def groq_response(prompt, model, api_key):
    client = Groq(
        api_key=api_key,
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model,
    )

    return chat_completion.choices[0].message.content


def get_gemini_model():
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model_gemini = genai.GenerativeModel("gemini-1.5-flash")
    print(model_gemini)
    return model_gemini


def get_palm_model():
    genai.configure(api_key="AIzaSyAHGBhlTLsFArveuwIYk5gFH9ulBt8nc8o")
    models = [
        m
        for m in genai.list_models()
        if "generateText" in m.supported_generation_methods
    ]
    model_palm = models[0].name
    print(model_palm)
    return model_palm


def get_gpt35_model():
    return "gpt-3.5-turbo-0125"


def get_gpt4omini_model():
    return "gpt-4o-mini"


def get_llama_model():
    return "llama3-70b-8192"


def get_mixtral_model():
    return "mixtral-8x7b-32768"


def create_gpt_request(prompt, count, model):
    req = {}

    messages = []

    message1 = {}
    message2 = {}
    message1["role"] = "system"
    message1["content"] = "You are a helpful assistant."
    message2["role"] = "user"
    message2["content"] = prompt

    messages.append(message1)
    messages.append(message2)

    body = {}
    body["model"] = model
    body["messages"] = messages
    body["max_tokens"] = 4000

    id = "request-" + str(count)

    req["custom_id"] = id
    req["method"] = "POST"
    req["url"] = "/v1/chat/completions"
    req["body"] = body

    return req


def convertJsonToString(tab_json, dataset):
    table_string = ""
    if dataset in ["tatqa", "squall"]:
        row_str = ""
        for header_entry in tab_json["headers"]:
            row_str = row_str + "|\t" + header_entry + "\t"
        row_str = row_str + "|\t" + "\n"
        table_string += row_str
        row_num = 1
        while ("row" + str(row_num)) in tab_json.keys():
            row_str = ""
            for row_entry in tab_json["row" + str(row_num)]:
                row_str = row_str + "|\t" + row_entry + "\t"
            row_str = row_str + "|\t" + "\n"
            table_string += row_str
            row_num += 1
        table_string += "\n"

    if dataset in ["hitabs", "multihiertt"]:
        for ind, title in enumerate(tab_json["titles"]):
            table_string = f"Title : {title}\n"
            row_str = ""
            for header_entry in tab_json["tables"][ind]["headers"]:
                row_str = row_str + "|\t" + header_entry + "\t"
            row_str = row_str + "|\t" + "\n"
            table_string += row_str
            row_num = 1
            while ("row" + str(row_num)) in tab_json["tables"][ind].keys():
                row_str = ""
                for row_entry in tab_json["tables"][ind]["row" + str(row_num)]:
                    row_str = row_str + "|\t" + row_entry + "\t"
                row_str = row_str + "|\t" + "\n"
                table_string += row_str
                row_num += 1
            table_string += "\n"
    return table_string


# def extract_code(response):
#     # Extract the code
#     code_match = re.search(r'```python(.*?)```', response, re.DOTALL)
#     if code_match:
#         return code_match.group(1).strip()
#     else:
#         return response.strip()


def extract_code(response):
    # Extract the code

    # if not ("Done" in response or "done" in response):
    #     return "print('Incomplete python code')"
    response = response.strip()

    python_blocks = re.findall(r"```python(.*?)```", response, re.DOTALL)
    if python_blocks:
        code = "\n".join(python_blocks)
        # code = python_blocks[-1].strip()
        return code
    elif response[0] == "#":
        return response
    else:
        return None


def get_code_output(code, timeout=120):
    # Create a string stream to capture the output
    output_stream = io.StringIO()

    def handler(signum, frame):
        raise TimeoutError("Code execution timed out")

    signal.signal(signal.SIGALRM, handler)  # Set timeout handler
    signal.alarm(timeout)  # Set execution timeout
    try:
        # Execute the code within a context that redirects stdout to the string stream
        with contextlib.redirect_stdout(output_stream):
            exec(code)
        signal.alarm(0)
        # Retrieve the output from the string stream
        return output_stream.getvalue()
    except Exception as e:
        return f"Error: {str(e)}"


import signal
import contextlib

@contextlib.contextmanager
def time_limit(seconds):
    """
    Context manager to limit execution time of a block of code.
    """
    def signal_handler(signum, frame):
        raise TimeoutError("Calculation timed out")
        
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)  # Disable the alarm

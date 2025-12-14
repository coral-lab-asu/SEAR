import os

import pandas as pd
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from loguru import logger
from dotenv import load_dotenv
import argparse
import utils

SYS_PROMPT = '''You are an advanced AI assistant specialized in meta-reasoning and data analysis. Your role is to answer questions about tabular data using a structured, logical approach. Here are your key capabilities and instructions:

                                                                                        1. Analyze the given table data carefully, extracting all relevant information.

                                                                                        2. Use a step-by-step reasoning process to break down and solve complex problems.

                                                                                        3. When appropriate, write Python code to perform calculations or data manipulation.

                                                                                        4. Provide clear, concise explanations for each step of your reasoning process.

                                                                                        5. Format your final answer as "Final Answer: [Your answer here]"

                                                                                        6. Adapt your approach based on the complexity of the question - use simpler methods for straightforward queries and more detailed analysis for complex ones.

                                                                                        7. If the table or question is unclear, ask for clarification before proceeding.

                                                                                        8. Maintain a formal, instructional tone in your responses.

                                                                                        9. Do not make assumptions beyond the given data. If critical information is missing, state this in your response.

                                                                                        10. Be prepared to handle a wide range of table formats and subject matters.

                                                                                        Remember, your goal is to provide accurate, well-reasoned answers while clearly demonstrating your thought process. Good luck!'''#, generation_config={"response_mime_type": "application/json"})

def test_gemini():

    load_dotenv()

    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    model = genai.GenerativeModel(model_name="gemini-1.5-pro")
    response = model.generate_content("What is the meaning of life?")
    print(response.text)


def run_qa(dataset, rows=30, from_index=0):

    reasoning_types = ['COT', 'Decomposition', 'Evidence', 'POT', 'Faithful']

    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY2'))
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")#, generation_config={"response_mime_type": "application/json"})

    for reasoning_type in reasoning_types[2:5]:
        index = from_index

        _ = logger.add(f"{dataset}_qa.log", format="{time} {level} {message}", level="DEBUG")

        response_file = f'./responses/New/{dataset}_{reasoning_type.lower()}_results.csv'

        for table_id, prompt, answer, question in utils.get_prompts(dataset=dataset, 
                                                                        reasoning=reasoning_type,run_all=True,     
                                                                        from_index=from_index):
            response = model.generate_content(prompt, 
                                                  safety_settings={
                                                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                                                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                                    })

            logger.debug(f"Reasoning Type: {reasoning_type}, Index: {index}, Question: {question}, Response: {response}")
            
            try:
                utils.append_response_to_file(index, table_id, question, str(response.text), answer, response_file)
            except Exception as e:
                logger.error(f"Error appending response to file at index {index}: {e}")

            index += 1
    
    logger.remove()
    return True


def run_meta_qa(dataset, reasoning, **kwargs):

    _ = logger.add(f"{dataset}__META_qa.log", format="{time} {level} {message}", level="DEBUG")
    index = 0

    meta = kwargs.get('meta', False)

    if meta:
        response_file = f'./responses/New/{dataset}_meta_results.csv'
    else:
        response_file = f'./responses/New/{dataset}_{reasoning.lower()}_results.csv'

    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY2'))
    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYS_PROMPT)


    for table_id, prompt, answer, question in utils.get_prompts(dataset, reasoning=reasoning, **kwargs):
        try:
            print(question)
            # response = response = model.generate_content(prompt, 
            #                                       safety_settings={
            #                                             HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            #                                             HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            #                                             HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            #                                             HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            #                                         })
            #utils.append_response_to_file(index=index, table_id=table_id, question=question, response=str(response.text), answer=answer, file_path=response_file)
            #logger.debug(f"Index: {index}, Question: {question}, Response: {response.text}", 'Answer: ', answer)
        except Exception as e:
            logger.error(f"Error querying API at index {index}: {e}")

        index += 1

    logger.remove()
    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate prompts with meta template')
    parser.add_argument('--dataset', type=str, default='fetaqa', help='Dataset name')
    parser.add_argument('--reasoning', type=str, default='COT', help='Reasoning type')
    parser.add_argument('--rows', type=int, default=5000, help='Number of rows to generate')
    parser.add_argument('--random', type=bool, default=False, help='Generate random rows')
    parser.add_argument('--meta', type=bool, default=False, help='Generate meta prompts')
    parser.add_argument('--from_index', type=int, default=0, help='Start from index')

    args = parser.parse_args()
    run_meta_qa(dataset=args.dataset, reasoning=args.reasoning, rows=args.rows, random=args.random, from_index=args.from_index, meta=args.meta)

    #Exception encountered: Invalid operation: The `response.text` quick accessor requires the response to contain a valid `Part`, but none were returned. Please check the `candidate.safety_ratings` to determine if the response was blocked.
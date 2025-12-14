import os
import argparse
import time

from groq import Groq

from loguru import logger
from dotenv import load_dotenv

import utils

def get_groq():

    load_dotenv()
    return Groq(api_key=os.environ.get("GROQ_API_KEY6"))


def run_groq_qa(dataset, model, reason_type,rows=10, **kwargs):

    random = kwargs.get('random', False)
    demo = kwargs.get('demo', False)
    run_all = False if demo else True
    from_index = kwargs.get('from_index', 0)

    reasoning_types = ['COT','Decomposition', 'Evidence', 'Faithful', 'POT']

    client = get_groq()
    
    index = from_index

    _ = logger.add(f"{dataset}_groq_qa.log", format="{time} {level} {message}", level="DEBUG")

    if not demo:

        response_file = f'./responses/{model}/{dataset}/{reason_type.lower()}_results.csv'

    else:
        response_file = f'./responses/{model}/demo/{dataset}_{reason_type.lower()}_results.csv'

    for table_id, prompt, answer, question in utils.get_prompts(dataset=dataset, 
                                                                    reasoning=reason_type, 
                                                                    from_index=from_index,
                                                                    rows=rows, 
                                                                    random=random, 
                                                                    run_all=run_all):
            
        try:                                          
            chat_completion = client.chat.completions.create(
                messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                model=model,
            )

            response_text = chat_completion.choices[0].message.content if chat_completion.choices else "No response"
            logger.debug(f"Reasoning Type: {reason_type}, Index: {index}, Question: {question}, Response: {response_text}")
                #time.sleep(0.5)

        except Exception as e:
            logger.error(f"Error generating response for index {index}, {question}: {e}")
            
        try:
            utils.append_response_to_file(index, table_id, question, response_text, answer, response_file)
        except Exception as e:
            logger.error(f"Error appending response to file at index {index}: {e}")

        index += 1
    
    logger.remove()
    return True

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Run Groq QA')
    parser.add_argument('--demo', type=bool, default=False, help='Run in demo mode')
    parser.add_argument('--dataset', type=str, default='fetaqa', help='Dataset to use')
    parser.add_argument('--rows', type=int, default=3, help='Number of rows to process')
    parser.add_argument('--from_index', type=int, default=0, help='Index to start processing from')
    parser.add_argument('--model', type=str, default='mixtral-8x7b-32768', help='Model to use')
    parser.add_argument('--random', type=bool, default=False, help='To use random rows or not')
    parser.add_argument('--reason', type=str, default='COT', help='Reasoning type to use')

    args = parser.parse_args()

    if args.model == 'llama':
        args.model = 'llama3-70b-8192'

    else:
        args.model = 'mixtral-8x7b-32768'

    kwargs = {
        'random': args.random,
        'rows': args.rows,
        'from_index': args.from_index,
        'demo': args.demo,
    }

    script_dir = os.path.dirname(os.path.abspath(__file__))
    response_dir = os.path.join(script_dir, 'responses')

    model_dir = os.path.join(response_dir, args.model)

    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print(f"Created directory: {model_dir}")

    if args.demo:
        
        demo_dir = os.path.join(model_dir, 'demo')

        if not os.path.exists(demo_dir):
            os.makedirs(demo_dir)
            print(f"Created demo directory: {demo_dir}")

    else:
        dataset_dir = os.path.join(model_dir, args.dataset)

        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
            print(f"Created dataset directory: {dataset_dir}")

        print(f'Running Groq QA for dataset {args.dataset} starting from index {args.from_index} rows using model {args.model} in demo mode')
        run_groq_qa(dataset=args.dataset, reason_type=args.reason, model=args.model, **kwargs)
        print('Done')

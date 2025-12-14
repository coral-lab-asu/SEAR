import sys
import os
import concurrent.futures

current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, 'utils')
sys.path.append(utils_dir)

prompts_dir = os.path.join(current_dir, '../prompts')
sys.path.append(prompts_dir)

import utils
import tatqa_prompts
import dynamic_prompts
import time
import ast
import pandas as pd
import json
from tqdm import tqdm

def run_cot(df_tatqa, table_dict_tatqa, output_folder, model, model_name):
    input_prompts_cot = []
    gemini_cot_responses = []
    llama_cot_responses = []
    mixtral_cot_responses = []
    gpt_requests_cot = []
    #print(len(df_tatqa))
    groq_api_key = os.environ.get("GROQ_API_KEY")
    for ind, row in tqdm(df_tatqa.iterrows()):
        table_str = utils.convertJsonToString(table_dict_tatqa[ast.literal_eval(row['table'])['uid']], 'tatqa')
        question = row['question']
        text = row['text']

        input_prompt = tatqa_prompts.get_prompt_cot_tatqa(table_str, text, question)
        input_prompts_cot.append(input_prompt)
        #print(input_prompt)

        if model_name=='gpt35' or model_name=='gpt4omini':
            gpt_requests_cot.append(utils.create_gpt_request(input_prompt, ind, model=model))
        
        if model_name=='gemini':
            itr=0
            while True:
                try:
                    if itr == 3:
                        result_gemini = "res"
                    else:
                        result_gemini = utils.gemini_response(input_prompt, model)
                    break
                except:
                    itr += 1
                    print("....halt....")
                    time.sleep(20)
            gemini_cot_responses.append(result_gemini)

        if model_name=='llama':
            itr=0
            while True:
                try:
                    if itr == 3:
                        result_llama = "res"
                    else:
                        result_llama = utils.groq_response(input_prompt, model, groq_api_key)
                    break
                except:
                    itr += 1
                    print("....halt....")
                    time.sleep(20)
            llama_cot_responses.append(result_llama)

        if model_name=='mixtral':
            itr=0
            while True:
                try:
                    if itr == 3:
                        result_mixtral = "res"
                    else:
                        result_mixtral = utils.groq_response(input_prompt, model, groq_api_key)
                    break
                except:
                    itr += 1
                    print("....halt....")
                    time.sleep(20)
            mixtral_cot_responses.append(result_mixtral)

    if model_name=='gpt35' or model_name=='gpt4omini':        
      output_file = output_folder + 'tatqa_cot_requests.jsonl'
      # Write each JSON dictionary to a new line in the file
      with open(output_file, 'w') as file:
          for item in gpt_requests_cot:
              json.dump(item, file)
              file.write('\n')
      print(f'\nData successfully written to {output_file}\n')

    if model_name=='gemini':
        df_cot_response_tatqa = df_tatqa
        df_cot_response_tatqa['input_prompt'] = input_prompts_cot
        df_cot_response_tatqa['response'] = gemini_cot_responses
        #df_cot_response_tatqa.head(5)
        output_file = output_folder + 'tatqa_cot_response.csv'
        print(f'\nSaving file {output_file}\n')
        df_cot_response_tatqa.to_csv(output_file, index=False)

    if model_name=='llama':
        df_cot_response_tatqa = df_tatqa
        df_cot_response_tatqa['input_prompt'] = input_prompts_cot
        df_cot_response_tatqa['response'] = llama_cot_responses
        #df_cot_response_tatqa.head(5)
        output_file = output_folder + 'tatqa_cot_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_cot_response_tatqa.to_csv(output_file, index=False)

    if model_name=='mixtral':
        df_cot_response_tatqa = df_tatqa
        df_cot_response_tatqa['input_prompt'] = input_prompts_cot
        df_cot_response_tatqa['response'] = mixtral_cot_responses
        #df_cot_response_tatqa.head(5)
        output_file = output_folder + 'tatqa_cot_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_cot_response_tatqa.to_csv(output_file, index=False)

def run_evidence(df_tatqa, table_dict_tatqa, output_folder, model, model_name):
    gemini_evidence_responses = []
    llama_evidence_responses = []
    mixtral_evidence_responses = []
    input_prompts_evidence = []
    gpt_requests_evidence = []
    groq_api_key = os.environ.get("GROQ_API_KEY")
    for ind, row in tqdm(df_tatqa.iterrows()):
        table_str = utils.convertJsonToString(table_dict_tatqa[ast.literal_eval(row['table'])['uid']], 'tatqa')
        question = row['question']
        text = row['text']

        input_prompt = tatqa_prompts.get_prompt_evidence_tatqa(table_str, text, question)
        input_prompts_evidence.append(input_prompt)
        #print(input_prompt)
        
        if model_name=='gpt35' or model_name=='gpt4omini':
            gpt_requests_evidence.append(utils.create_gpt_request(input_prompt, ind, model=model))

        if model_name=='gemini':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_gemini = "res"
                        else:
                            result_gemini = utils.gemini_response(input_prompt, model)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            gemini_evidence_responses.append(result_gemini)

        if model_name=='llama':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_llama = "res"
                        else:
                            result_llama = utils.groq_response(input_prompt, model, groq_api_key)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            llama_evidence_responses.append(result_llama)

        if model_name=='mixtral':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_mixtral = "res"
                        else:
                            result_mixtral = utils.groq_response(input_prompt, model, groq_api_key)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            mixtral_evidence_responses.append(result_mixtral)

    if model_name=='gpt35' or model_name=='gpt4omini':        
      output_file = output_folder + 'tatqa_evidence_requests.jsonl'
      # Write each JSON dictionary to a new line in the file
      with open(output_file, 'w') as file:
          for item in gpt_requests_evidence:
              json.dump(item, file)
              file.write('\n')
      print(f'\nData successfully written to {output_file}\n')

    if model_name=='gemini':
        df_evidence_response_tatqa = df_tatqa
        df_evidence_response_tatqa['input_prompt'] = input_prompts_evidence
        df_evidence_response_tatqa['response'] = gemini_evidence_responses
        output_file = output_folder + 'tatqa_evidence_response.csv'
        print(f'\nSaving file {output_file}\n')
        df_evidence_response_tatqa.to_csv(output_file, index=False) 

    if model_name=='llama':
        df_evidence_response_tatqa = df_tatqa
        df_evidence_response_tatqa['input_prompt'] = input_prompts_evidence
        df_evidence_response_tatqa['response'] = llama_evidence_responses
        output_file = output_folder + 'tatqa_evidence_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_evidence_response_tatqa.to_csv(output_file, index=False) 

    if model_name=='mixtral':
        df_evidence_response_tatqa = df_tatqa
        df_evidence_response_tatqa['input_prompt'] = input_prompts_evidence
        df_evidence_response_tatqa['response'] = mixtral_evidence_responses
        output_file = output_folder + 'tatqa_evidence_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_evidence_response_tatqa.to_csv(output_file, index=False)

def run_decomposition(df_tatqa, table_dict_tatqa, output_folder, model, model_name):
    gemini_decomposition_responses = []
    llama_decomposition_responses = []
    mixtral_decomposition_responses = []
    input_prompts_decomposition = []
    gpt_requests_decomposition = []
    groq_api_key = os.environ.get("GROQ_API_KEY")
    for ind, row in tqdm(df_tatqa.iterrows()):
        table_str = utils.convertJsonToString(table_dict_tatqa[ast.literal_eval(row['table'])['uid']], 'tatqa')
        question = row['question']
        text = row['text']

        input_prompt = tatqa_prompts.get_prompt_decomposition_tatqa(table_str, text, question)
        input_prompts_decomposition.append(input_prompt)
        #print(input_prompt)
        
        if model_name=='gpt35' or model_name=='gpt4omini':
            gpt_requests_decomposition.append(utils.create_gpt_request(input_prompt, ind, model=model))

        if model_name=='gemini':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_gemini = "res"
                        else:
                            result_gemini = utils.gemini_response(input_prompt, model)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            gemini_decomposition_responses.append(result_gemini)

        if model_name=='llama':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_llama = "res"
                        else:
                            result_llama = utils.groq_response(input_prompt, model, groq_api_key)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            llama_decomposition_responses.append(result_llama)

        if model_name=='mixtral':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_mixtral = "res"
                        else:
                            result_mixtral = utils.groq_response(input_prompt, model, groq_api_key)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            mixtral_decomposition_responses.append(result_mixtral)

    if model_name=='gpt35' or model_name=='gpt4omini':        
      output_file = output_folder + 'tatqa_decomposition_requests.jsonl'
      # Write each JSON dictionary to a new line in the file
      with open(output_file, 'w') as file:
          for item in gpt_requests_decomposition:
              json.dump(item, file)
              file.write('\n')
      print(f'\nData successfully written to {output_file}\n')

    if model_name=='gemini':
        df_decomposition_response_tatqa = df_tatqa
        df_decomposition_response_tatqa['input_prompt'] = input_prompts_decomposition
        df_decomposition_response_tatqa['response'] = gemini_decomposition_responses
        output_file = output_folder + 'tatqa_decomposition_response.csv'
        print(f'\nSaving file {output_file}\n')
        df_decomposition_response_tatqa.to_csv(output_file, index=False)

    if model_name=='llama':
        df_decomposition_response_tatqa = df_tatqa
        df_decomposition_response_tatqa['input_prompt'] = input_prompts_decomposition
        df_decomposition_response_tatqa['response'] = llama_decomposition_responses
        output_file = output_folder + 'tatqa_decomposition_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_decomposition_response_tatqa.to_csv(output_file, index=False)

    if model_name=='mixtral':
        df_decomposition_response_tatqa = df_tatqa
        df_decomposition_response_tatqa['input_prompt'] = input_prompts_decomposition
        df_decomposition_response_tatqa['response'] = mixtral_decomposition_responses
        output_file = output_folder + 'tatqa_decomposition_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_decomposition_response_tatqa.to_csv(output_file, index=False)

def run_pot(df_tatqa, table_dict_tatqa, output_folder, model, model_name):
    gemini_pot_responses = []
    llama_pot_responses = []
    mixtral_pot_responses = []
    input_prompts_pot = []
    gpt_requests_pot = []
    pot_code_outputs = []
    groq_api_key = os.environ.get("GROQ_API_KEY")
    for ind, row in tqdm(df_tatqa.iterrows()):
        table_str = utils.convertJsonToString(table_dict_tatqa[ast.literal_eval(row['table'])['uid']], 'tatqa')
        question = row['question']
        text = row['text']

        input_prompt = tatqa_prompts.get_prompt_pot_tatqa(table_str, text, question)
        input_prompts_pot.append(input_prompt)
        #print(input_prompt)
        
        if model_name=='gpt35' or model_name=='gpt4omini':
            gpt_requests_pot.append(utils.create_gpt_request(input_prompt, ind, model=model))

        if model_name=='gemini':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_gemini = "res"
                        else:
                            result_gemini = utils.gemini_response(input_prompt, model)
                            # print()
                            # print(result_gemini)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            gemini_pot_responses.append(result_gemini)
            code = utils.extract_code(result_gemini)
            out = utils.get_code_output(code)
            pot_code_outputs.append(out)
            # print(out)
            # print()

        if model_name=='llama':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_llama = "res"
                        else:
                            result_llama = utils.groq_response(input_prompt, model, groq_api_key)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            llama_pot_responses.append(result_llama)
            code = utils.extract_code(result_llama)
            out = utils.get_code_output(code)
            #print(out)
            pot_code_outputs.append(out)

        if model_name=='mixtral':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_mixtral = "res"
                        else:
                            result_mixtral = utils.groq_response(input_prompt, model, groq_api_key)
                            # print()
                            # print(result_gemini)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            mixtral_pot_responses.append(result_mixtral)
            code = utils.extract_code(result_mixtral)
            out = utils.get_code_output(code)
            pot_code_outputs.append(out)


    if model_name=='gpt35' or model_name=='gpt4omini':        
      output_file = output_folder + 'tatqa_pot_requests.jsonl'
      # Write each JSON dictionary to a new line in the file
      with open(output_file, 'w') as file:
          for item in gpt_requests_pot:
              json.dump(item, file)
              file.write('\n')
      print(f'\nData successfully written to {output_file}\n')

    if model_name=='gemini':
        df_pot_response_tatqa = df_tatqa
        df_pot_response_tatqa['input_prompt'] = input_prompts_pot
        df_pot_response_tatqa['response'] = gemini_pot_responses
        df_pot_response_tatqa['output'] = pot_code_outputs
        output_file = output_folder + 'tatqa_pot_response.csv'
        print(f'\nSaving file {output_file}\n')
        df_pot_response_tatqa.to_csv(output_file, index=False)

    if model_name=='llama':
        df_pot_response_tatqa = df_tatqa
        df_pot_response_tatqa['input_prompt'] = input_prompts_pot
        df_pot_response_tatqa['response'] = llama_pot_responses
        df_pot_response_tatqa['output'] = pot_code_outputs
        output_file = output_folder + 'tatqa_pot_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_pot_response_tatqa.to_csv(output_file, index=False)

    if model_name=='mixtral':
        df_pot_response_tatqa = df_tatqa
        df_pot_response_tatqa['input_prompt'] = input_prompts_pot
        df_pot_response_tatqa['response'] = mixtral_pot_responses
        df_pot_response_tatqa['output'] = pot_code_outputs
        output_file = output_folder + 'tatqa_pot_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_pot_response_tatqa.to_csv(output_file, index=False)

def run_faithful(df_tatqa, table_dict_tatqa, output_folder, model, model_name):
    gemini_faithful_responses = []
    llama_faithful_responses = []
    mixtral_faithful_responses = []
    input_prompts_faithful = []
    gpt_requests_faithful = []
    faithful_code_outputs = []
    groq_api_key = os.environ.get("GROQ_API_KEY")
    for ind, row in tqdm(df_tatqa.iterrows()):
        table_str = utils.convertJsonToString(table_dict_tatqa[ast.literal_eval(row['table'])['uid']], 'tatqa')
        question = row['question']
        text = row['text']

        input_prompt = tatqa_prompts.get_prompt_faithful_tatqa(table_str, text, question)
        input_prompts_faithful.append(input_prompt)
        #print(input_prompt)
        
        if model_name=='gpt35' or model_name=='gpt4omini':
            gpt_requests_faithful.append(utils.create_gpt_request(input_prompt, ind, model=model))

        if model_name=='gemini':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_gemini = "res"
                        else:
                            result_gemini = utils.gemini_response(input_prompt, model)
                            print(result_gemini)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            gemini_faithful_responses.append(result_gemini)
            code = utils.extract_code(result_gemini)
            out = utils.get_code_output(code)
            print(out)
            faithful_code_outputs.append(out)

        if model_name=='llama':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_llama = "res"
                        else:
                            result_llama = utils.groq_response(input_prompt, model, groq_api_key)
                            print(result_llama)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            llama_faithful_responses.append(result_llama)
            code = utils.extract_code(result_llama)
            out = utils.get_code_output(code)
            #print(out)
            faithful_code_outputs.append(out)

        if model_name=='mixtral':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_mixtral = "res"
                        else:
                            result_mixtral = utils.groq_response(input_prompt, model, groq_api_key)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            mixtral_faithful_responses.append(result_mixtral)
            code = utils.extract_code(result_mixtral)
            out = utils.get_code_output(code)
            faithful_code_outputs.append(out)

    if model_name=='gpt35' or model_name=='gpt4omini':        
      output_file = output_folder + 'tatqa_faithful_requests.jsonl'
      # Write each JSON dictionary to a new line in the file
      with open(output_file, 'w') as file:
          for item in gpt_requests_faithful:
              json.dump(item, file)
              file.write('\n')
      print(f'\nData successfully written to {output_file}\n')

    if model_name=='gemini':
        df_faithful_response_tatqa = df_tatqa
        df_faithful_response_tatqa['input_prompt'] = input_prompts_faithful
        df_faithful_response_tatqa['response'] = gemini_faithful_responses
        df_faithful_response_tatqa['output'] = faithful_code_outputs
        output_file = output_folder + 'tatqa_faithful_response.csv'
        print(f'\nSaving file {output_file}\n')
        df_faithful_response_tatqa.to_csv(output_file, index=False)

    if model_name=='llama':
        df_faithful_response_tatqa = df_tatqa
        df_faithful_response_tatqa['input_prompt'] = input_prompts_faithful
        df_faithful_response_tatqa['response'] = llama_faithful_responses
        df_faithful_response_tatqa['output'] = faithful_code_outputs
        output_file = output_folder + 'tatqa_faithful_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_faithful_response_tatqa.to_csv(output_file, index=False)

    if model_name=='mixtral':
        df_faithful_response_tatqa = df_tatqa
        df_faithful_response_tatqa['input_prompt'] = input_prompts_faithful
        df_faithful_response_tatqa['response'] = mixtral_faithful_responses
        df_faithful_response_tatqa['output'] = faithful_code_outputs
        output_file = output_folder + 'tatqa_faithful_response1.csv'
        print(f'\nSaving file {output_file}\n')
        df_faithful_response_tatqa.to_csv(output_file, index=False)

def process_row(index, row, table_dict_tatqa, model, model_name):
    try:
        #print(f"Processing row {index}...")
        table_str = utils.convertJsonToString(table_dict_tatqa[ast.literal_eval(row['table'])['uid']], 'tatqa')
        question = row['question']
        text = row['text']
        input_prompt = dynamic_prompts.get_dynamic_prompt_tatqa_2shot(table_str, text, question)
        #print(f"Generated input prompt: {input_prompt}")

        if model_name == 'gemini':
            itr = 0
            while True:
                try:
                    if itr == 3:
                        result_gemini = "res"
                    else:
                        result_gemini = utils.gemini_response(input_prompt, model)
                    break
                except Exception as e:
                    itr += 1
                    print(f"....halt.... {e}")
                    time.sleep(20)
                    if itr >= 3:
                        raise e

            code = utils.extract_code(result_gemini)
            dynamic_code_output = utils.get_code_output(code)
            # print(f"Generated response: {result_gemini}")
            # print(f"Generated code output: {dynamic_code_output}")

        return index, input_prompt, result_gemini, dynamic_code_output

    except Exception as e:
        print(f"Error processing row {index}: {e}")
        return index, None, None, None

def run_dynamic(df_tatqa, table_dict_tatqa, output_folder, model, model_name):
    gemini_dynamic_responses = []
    llama_dynamic_responses = []
    mixtral_dynamic_responses = []
    input_prompts_dynamic = []
    gpt_requests_dynamic = []
    dynamic_code_outputs = []
    groq_api_key = os.environ.get("GROQ_API_KEY")

    if model_name=='gemini':
        #print("inside run_dynamic")
        input_prompts_dynamic = {}
        gemini_dynamic_responses = {}
        dynamic_code_outputs = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            future_to_index = {
                executor.submit(process_row, index, row, table_dict_tatqa, model, model_name): index 
                for index, row in df_tatqa.iterrows()
            }

            for future in tqdm(concurrent.futures.as_completed(future_to_index), total=len(future_to_index)):
                index = future_to_index[future]
                try:
                    index, input_prompt, result_gemini, dynamic_code_output = future.result()
                    if input_prompt is not None:
                        input_prompts_dynamic[index] = input_prompt
                    if result_gemini is not None:
                        gemini_dynamic_responses[index] = result_gemini
                    if dynamic_code_output is not None:
                        dynamic_code_outputs[index] = dynamic_code_output
                except Exception as e:
                    print(f"Exception for index {index}: {e}")

        df_tatqa['input_prompt'] = df_tatqa.index.map(input_prompts_dynamic)
        df_tatqa['response'] = df_tatqa.index.map(gemini_dynamic_responses)
        df_tatqa['code_output'] = df_tatqa.index.map(dynamic_code_outputs)
            
        output_file = output_folder + 'tatqa_dynamic_response.csv'
        print(f'\nSaving file {output_file}\n')
        df_tatqa.to_csv(output_file, index=False)       
        return

    for ind, row in tqdm(df_tatqa.iterrows()):
        table_str = utils.convertJsonToString(table_dict_tatqa[ast.literal_eval(row['table'])['uid']], 'tatqa')
        question = row['question']
        text = row['text']

        input_prompt = dynamic_prompts.get_dynamic_prompt_tatqa_2shot(table_str, text, question)
        input_prompts_dynamic.append(input_prompt)
        #print(input_prompt)
        
        if model_name=='gpt35' or model_name=='gpt4omini':
            gpt_requests_dynamic.append(utils.create_gpt_request(input_prompt, ind, model=model))

        if model_name=='llama':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_llama = "res"
                        else:
                            result_llama = utils.groq_response(input_prompt, model, groq_api_key)
                            print(result_llama)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            llama_dynamic_responses.append(result_llama)
            code = utils.extract_code(result_llama)
            out = utils.get_code_output(code)
            #print(out)
            dynamic_code_outputs.append(out)

        if model_name=='mixtral':
            itr=0
            while True:
                    try:
                        if itr == 3:
                            result_mixtral = "res"
                        else:
                            result_mixtral = utils.groq_response(input_prompt, model, groq_api_key)
                        break
                    except:
                        itr += 1
                        print("....halt....")
                        time.sleep(20)
            mixtral_dynamic_responses.append(result_mixtral)
            code = utils.extract_code(result_mixtral)
            out = utils.get_code_output(code)
            dynamic_code_outputs.append(out)

    if model_name=='gpt35' or model_name=='gpt4omini':        
      output_file = output_folder + 'tatqa_dynamic_requests.jsonl'
      # Write each JSON dictionary to a new line in the file
      with open(output_file, 'w') as file:
          for item in gpt_requests_dynamic:
              json.dump(item, file)
              file.write('\n')
      print(f'\nData successfully written to {output_file}\n')

    if model_name=='llama':
        df_dynamic_response_tatqa = df_tatqa[['question','answer']]
        df_dynamic_response_tatqa['input_prompt'] = input_prompts_dynamic
        df_dynamic_response_tatqa['response'] = llama_dynamic_responses
        df_dynamic_response_tatqa['code_output'] = dynamic_code_outputs
        output_file = output_folder + 'tatqa_dynamic_response.csv'
        print(f'\nSaving file {output_file}\n')
        df_dynamic_response_tatqa.to_csv(output_file, index=False)

    if model_name=='mixtral':
        df_dynamic_response_tatqa = df_tatqa[['question','answer']]
        df_dynamic_response_tatqa['input_prompt'] = input_prompts_dynamic
        df_dynamic_response_tatqa['response'] = mixtral_dynamic_responses
        df_dynamic_response_tatqa['code_output'] = dynamic_code_outputs
        output_file = output_folder + 'tatqa_dynamic_response.csv'
        print(f'\nSaving file {output_file}\n')
        df_dynamic_response_tatqa.to_csv(output_file, index=False)

def run_tatqa(model_name, table_folder, input_file):
    #Loading the input file
    df_tatqa = pd.read_csv(input_file)
    df_tatqa = df_tatqa

    table_path = table_folder + 'tatqa_tables.json'
        
    #Loading the input table dictionary
    with open(table_path, 'r') as f:
        table_dict_tatqa = json.load(f)

    if model_name=='gemini':
        output_path = 'outputs/gemini_response_files/tatqa/'
        os.makedirs(output_path, exist_ok=True)
        model = utils.get_gemini_model()
    if model_name=='gpt35':
        output_path = 'outputs/gpt_request_files/tatqa/'
        os.makedirs(output_path, exist_ok=True)
        model = utils.get_gpt35_model()
    if model_name=='gpt4omini':
        output_path = 'outputs/gpt4omini_request_files/tatqa/'
        os.makedirs(output_path, exist_ok=True)
        model = utils.get_gpt4omini_model()
    if model_name=='llama':
        output_path = 'outputs/llama_response_files/tatqa/'
        os.makedirs(output_path, exist_ok=True)
        model = utils.get_llama_model()
    if model_name=='mixtral':
        output_path = 'outputs/mixtral_response_files/tatqa/'
        os.makedirs(output_path, exist_ok=True)
        model = utils.get_mixtral_model()

    print("\nRunning COT......\n")
    run_cot(df_tatqa, table_dict_tatqa, output_path, model, model_name)

    print("\nRunning Evidence Extraction......\n")
    run_evidence(df_tatqa, table_dict_tatqa, output_path, model, model_name)

    print("\nRunning Decomposition......\n")
    run_decomposition(df_tatqa, table_dict_tatqa, output_path, model, model_name)

    print("\nRunning POT......\n")
    run_pot(df_tatqa, table_dict_tatqa, output_path, model, model_name)

    print("\nRunning Faithful......\n")
    run_faithful(df_tatqa, table_dict_tatqa, output_path, model, model_name)

    print("\nRunning Dynamic Prompting......\n")
    run_dynamic(df_tatqa, table_dict_tatqa, output_path, model, model_name)
        




        

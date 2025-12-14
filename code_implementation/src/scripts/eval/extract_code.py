import re
import os

import io
import contextlib

import argparse

import pandas as pd

def extract_code(response):
    # Extract the code
    code_match = re.search(r'⁠  python(.*?)  ⁠', response, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    else:
        return response.strip()
    
def extract_code2(response):
    pattern = r"```python\n([\s\S]*?)\n```"

# Find all matches in the text
    matches = re.findall(pattern, response)

    # Assuming you want the first match
    if matches:
        code_block = matches[0]
        return code_block
    else:
        print("No code block found")

def extract_code_os(text):
    pattern = r'```(?:python)?\n([\s\S]*?print\([^)]*\))(?:\n|$)'

    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)

    clean_pattern = r'""([^"]*?)""'
    cleaned_blocks = [re.sub(clean_pattern, r'"\1"', block) for block in matches]

    backslash_pattern = r'\\(?!["\'\\])'
    cleaned_blocks = [re.sub(backslash_pattern, '', block) for block in cleaned_blocks]

    if matches and all(cleaned_blocks):
        combined_code = '\n'.join(code.strip() for code in cleaned_blocks)
        return combined_code
    
    return None

def extract_code_meta(text):
    # Pattern to match Python code blocks
    pattern = r'```python\n([\s\S]*?)```'
    
    # Find all matches
    matches = re.findall(pattern, text, re.DOTALL)
    
    if matches:
        # Combine all code blocks and fix indentation
        combined_code = ''
        for match in matches:
            # Remove common leading whitespace from each line
            lines = match.split('\n')
            if lines:
                min_indent = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
                dedented_lines = [line[min_indent:] if line.strip() else '' for line in lines]
                combined_code += '\n'.join(dedented_lines) + '\n\n'
        
        # Clean up any remaining markdown artifacts and extra whitespace
        combined_code = re.sub(r'^#+\s*.*$', '', combined_code, flags=re.MULTILINE)
        combined_code = combined_code.strip()
        
        return combined_code
    else:
        return None

def extract_python_code(text):
    # Regex pattern to match Python code blocks
    pattern = r'```(?:python)?\s*\n((?:(?!```)[\s\S])*?(?:^|\n)\s*print\s*\([^)]*\)(?:(?!```)[\s\S])*?)(?:```|\Z)'
    
    # Find all matches
    matches = re.finditer(pattern, text, re.MULTILINE)
    
    # Combine all code blocks
    combined_code = []
    for match in matches:
        code_block = match.group(1).strip()
        combined_code.append(code_block)
    
    # Join the code blocks with newlines
    final_code = '\n\n'.join(combined_code)
    
    # Clean up any remaining markdown artifacts and extra whitespace
    final_code = re.sub(r'^\s*#.*$', '', final_code, flags=re.MULTILINE)  # Remove full-line comments
    final_code = re.sub(r'\n{3,}', '\n\n', final_code)  # Replace multiple newlines with double newlines
    final_code = final_code.strip()
    
    return final_code if final_code else None

def get_code_output(code):
    output_stream = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_stream):
            exec(code)
        value = output_stream.getvalue()
        return value
    except Exception as e:
        print(f"Error: {e}, for\n{code}")
        return "CODE ERROR"

def process_csv_file(file_path, extract):
    df = pd.read_csv(file_path)

    if 'response' in df.columns:
        for index, row in df.iterrows():

            extracted_code = extract(row['response'])
            print(extracted_code)
            
            if extracted_code is not None:
                
                output = get_code_output(extracted_code)
                print(output)
            
                df.at[index, 'code_output'] = output
                df.at[index, 'output'] = None

            else:
                print("No code found")

        df.to_csv(file_path, index=False)

def main():

    parser = argparse.ArgumentParser(description='Process some files.')
    parser.add_argument('--input_path', default='', type=str, help='Input Path')
    parser.add_argument('--model', required=True, type=str, help='Enter which model to extract code for.')
    
    args = parser.parse_args()
    full_path = args.input_path
    
    
    try:
        for file in os.listdir(full_path):
                
            if ('POT'.lower() in os.path.basename(file).lower() 
                    or 'Faithful'.lower() in os.path.basename(file).lower() 
                    or 'meta'.lower() in os.path.basename(file).lower()) and file.endswith(".csv"):
                    
                file_path = os.path.join(full_path, file)

                print(f"Processing {file_path}")

                if args.model == 'llama':
                    process_csv_file(file_path, extract_code_os)
                else:
                    process_csv_file(file_path, extract_python_code)

                if 'meta'.lower() in os.path.basename(file).lower():
                    process_csv_file(file_path, extract_python_code)
                    

    except FileNotFoundError:
        print(f"Directory not found: {full_path}")


def process_meta_responses():
    parser = argparse.ArgumentParser(description='Process files without subdirectories.')
    parser.add_argument('--input_path', default='', type=str, help='Input Path')
    

    args = parser.parse_args()

    try:
        for file in os.listdir(args.input_path):

            if file.endswith(".csv"):

                file_path = os.path.join(args.input_path, file)
                process_csv_file(file_path, extract_code_meta)
                
    except Exception as e:
        print(f"Error processing files: {e}")

def drop_output(file_path):
    df = pd.read_csv(file_path)
    df.drop('output', axis=1, inplace=True)
    df.to_csv(file_path, index=False)

def drop_():
    parser = argparse.ArgumentParser(description='Process some files.')
    parser.add_argument('--input_path', default='', type=str, help='Input Path')
    args = parser.parse_args()

    full_path = args.input_path
    
    
    try:
        for file in os.listdir(full_path):
            file_lower = os.path.basename(file).lower()
            if 'pot' in file_lower or 'faithful' in file_lower:
                file_path = os.path.join(full_path, file)
                print(f"Processing {file_path}")
                drop_output(file_path)

    except FileNotFoundError:
        print(f"Directory not found: {full_path}")
        

if __name__ == '__main__':
    #drop_()
    main()
    #process_meta_responses()

import argparse
import os
import sys
import pandas as pd
from tqdm import tqdm
import time
import glob
import concurrent.futures

from dotenv import load_dotenv

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from loguru import logger

current_dir = os.path.dirname(os.path.abspath(__file__))

prompts_dir = os.path.join(current_dir, '../prompts')
sys.path.append(prompts_dir)

def get_prompt_extraction(question, answer):
    return f'''You are given with a question and answer. Your task is to respond by extracting the final answer from the overall answer.
Instructions:
1. Provide the answer in a straigtforward manner and keep it within 1 to 10 words.
2. Respond only with the information provided. Do not use external knowledge in your response.
3. If there are multiple answers, Response should be a list of all answers.
4. If a conclusive answer cannot be determined, respond with "Not enough information provided."

Few Examples of question and answers are given with Response for reference:

Example 1:
Question: which game did the opponent score only 7 points ?
Answer: 
Subquestions:
1. What is the column containing the opponent names and their corresponding scores?
2. Which game had the opponent score only 7 points?

Let's answer each subquestion:

Subquestion 1:
What is the column containing the opponent names and their corresponding scores?
Answer:
- The opponent names are in the "c3_raw" column.
- The opponent scores are in the "c7_number2" column.

Subquestion 2:
Which game had the opponent score only 7 points?
Answer:
- The opponent score of 7 points corresponds to the 11th game (index 10).
- Checking the corresponding opponent in the "c3_raw" column, it was "san diego state".

Final Answer: San Diego State

Response: San Diego State

Example 2:
Question: how many total seasons are given in the chart ?
Answer:
Subquestion 1: How many unique season entries are present in the table? (Independent)

Subquestion 2: Do all the season entries represent unique seasons, or are there any repeated seasons? (Dependent on sq1)

Subquestion 3: If there are repeated seasons, how many distinct seasons are there excluding any duplicates? (Dependent on sq2)

Let's answer each subquestion:

Subquestion 1: How many unique season entries are present in the table? (Independent)
Answer: 
- The season data is present in the column labeled "c1".
- Count the number of unique entries in the "c1" column.

Subquestion 2: Do all the season entries represent unique seasons, or are there any repeated seasons? (Dependent on sq1)
Answer:
- Check if all season entries are unique or if there are any duplicates present.

Subquestion 3: If there are repeated seasons, how many distinct seasons are there excluding any duplicates? (Dependent on sq2)
Answer:
- If there are repeated seasons, count the total number of distinct seasons after removing duplicates.

Final Answer: {{Answer}}

Your final answer will consider the number of distinct seasons present in the table without any repetitions.

Response: Not enough information provided.

Example 3:
Question: how many games did they win in 2009 ?
Answer: 
### Extracted Evidence:
1. **`c2_year`**: Contains the year of the game.
   - `c2_year`: [2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009, 2009]
   
2. **`c5_result`**: Contains the result of each game.
   - `c5_result`: ["w", "l", "l", "w", "w", "w", "l", "l", "w", "l", "w", "l", "l", "l", "l", "w"]

### Final Answer:
The number of games won in 2009 can be found by counting the number of "w" (win) entries in the `c5_result` column for the year 2009.

**Final Answer: 6 games were won in 2009.**

Response: 6

Example 4:
Question: how many times was the mean value of resps among families at the top higher than those at the bottom of the distribution in 1999?
Answer: 
Given the table detailing registered education savings plan holdings of economic families with children across different categories and years, we are tasked with determining the difference in the mean value of RESP holdings between families at the top and bottom of the distribution in 1999.

From the data provided in the table for the year 1999:

- For families at the bottom of the income quintile:
  - Mean value of RESP: $746

- For families at the top of the income quintile:
  - Mean value of RESP: $3,134

To find the difference in mean value of RESP holdings between the top and bottom income quintiles in 1999:
$3,134 / $746 = approximately 4.2 times

Thus, the mean value of RESP holdings among families at the top was approximately 4.2 times higher than those at the bottom of the distribution in 1999.

Final Answer: 4.2 times

Response: 4.2

Example 5:
Question: which league did towers play for brentford in 1958-59?
Answer: 
Based on the provided table, the relevant rows and columns for the question are as follows:

| Club      | Season | League           | Apps | Goals | FA Cup | League Cup | Total  |
|------------|--------|------------------|------|-------|--------|------------|--------|
| Brentford | 1958-59 | Third Division   | 46   | 32    | 4      | 5          | 50     |

Final Answer: Towers played for Brentford in the Third Division in 1958-59.

Response: Third Division

Example 6:
Question: In which years was the selected financial data provided?
Answer:
Subquestion 1: What is the year for the selected financial data provided for Net sales?
Answer: The selected financial data for Net Sales was provided for the years 2015 to 2019.

Subquestion 2: What is the year for the selected financial data provided for Gross profit?
Answer: The selected financial data for Gross Profit was provided for the years 2015 to 2019.

Subquestion 3: What is the year for the selected financial data provided for Net income from continuing operations?
Answer: The selected financial data for Net Income from Continuing Operations was provided for the years 2015 to 2019.

Subquestion 4: What is the year for the selected financial data provided for Total assets?
Answer: The selected financial data for Total Assets was provided for the years 2015 to 2019.

Subquestion 5: What is the year for the selected financial data provided for Long-term obligations?
Answer: The selected financial data for Long-term Obligations was provided for the years 2015 to 2019.

Subquestion 6: What is the year for the selected financial data provided for Other long-term liabilities?
Answer: The selected financial data for Other Long-term Liabilities was provided for the years 2015 to 2019.

Subquestion 7: What is the year for the selected financial data provided for Stockholders' equity?
Answer: The selected financial data for Stockholders' Equity was provided for the years 2015 to 2019.

Final Answer : The selected financial data was provided for the years 2015 to 2019.

Response: ['2015', '2016', '2017', '2018', '2019']

Example 7:
Question: What is the high sale and low sale of the first quarter of 2019 respectively? 
Answer:
Subquestion 1: What is the high sale price in the first quarter of 2019?
Answer: From the table, the high sale price in the first quarter of 2019 is $8.95.

Subquestion 2: What is the low sale price in the first quarter of 2019?
Answer: From the table, the low sale price in the first quarter of 2019 is $7.30.

Final Answer: High Sale Price: $8.95, Low Sale Price: $7.30

Response: ['$8.95','$7.30']

For the following question and answer provide your response:

Question: {question}
Answer:
{answer}

Response:'''

def get_gemini_model():
    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY2'))
    return genai.GenerativeModel(model_name="gemini-1.5-flash")

def gemini_response(prompt, model):
    try:
        response = model.generate_content(prompt, 
                                          safety_settings={
                                              HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                              HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                              HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                                              HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                                          })
        return response.text
    except Exception as e:
        logger.error(f"Error appending response to file: {e}")
        return None

def process_row(row, model):
    question = row['question']
    text_response = row['response']
    input_prompt = get_prompt_extraction(question, text_response)
    
    for _ in range(3):
        try:
            out = gemini_response(input_prompt, model)
            if out:
                return out
        except:
            time.sleep(20)
    
    return "res"

def extract_and_save(df, output_path, max_workers):
    model = get_gemini_model()

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {executor.submit(process_row, row, model): index for index, row in df.iterrows()}
        
        for future in tqdm(concurrent.futures.as_completed(future_to_index), total=len(df)):
            index = future_to_index[future]
            try:
                result = future.result()
                df.loc[index, 'output'] = result
            except Exception as e:
                logger.error(f"Error processing row at index {index}: {e}")

    df.to_csv(output_path, index=False)
    print(f"File after extraction saved successfully at: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_path', default='', type=str, help='Input Path')
    parser.add_argument('--max_workers', default=5, type=int, help='Maximum number of worker threads')
    parser.add_argument('--file', default='NONE', type=str, help='Log level')

    logger.add(f"gemini_error.log", format="{time} {level} {message}", level="DEBUG")

    args = parser.parse_args()
    INPUT_PATH = args.input_path
    MAX_WORKERS = args.max_workers

    csv_files = glob.glob(os.path.join(INPUT_PATH, '*.csv'))

    if args.file != 'NONE':
        #fetch a single file
        csv_files = [os.path.join(INPUT_PATH, args.file)]

    print(f"Running Extraction for: {INPUT_PATH}")

    for file in csv_files:
        if 'POT' not in os.path.basename(file) and 'Faithful' not in os.path.basename(file):
            data = pd.read_csv(file)
            print(f"Extracting for: {os.path.basename(file)}:")
            extract_and_save(data, str(file), MAX_WORKERS)
            print("\n" + "="*50 + "\n")
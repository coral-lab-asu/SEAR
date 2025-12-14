def get_s2_prompt(table, question, crucial_steps, text):
    return f"""

Your task is to comprehend the crucial steps for a given table and question, making each step more detailed and ensuring they effectively lead to the correct answer. 

Few Examples are given below with detailed steps by elaborating from the crucial steps. Interpret the examples and understand the task to comprehend the crucial steps according to the specific table, text and question to reach the answer efficiently.

Examples:

Example1:
Context:
### Škoda Car Sales from 2005 to 2013

| Model           | 2005   | 2006   | 2007   | 2008   | 2009   | 2010   | 2011   | 2012   | 2013   |
|-----------------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| Škoda Octavia   | 233,322 | 270,274 | 309,951 | 344,857 | 317,335 | 349,746 | 387,200 | 409,360 | 359,600 |
| Škoda Fabia     | 236,698 | 243,982 | 232,890 | 246,561 | 264,173 | 229,045 | 266,800 | 255,025 | 202,000 |
| Škoda Superb    | 22,091  | 20,989  | 20,530  | 25,645  | 44,548  | 98,873  | 116,700 | 106,847 | 94,400  |
| Škoda Roomster  |         | 14,422  | 66,661  | 57,467  | 47,152  | 32,332  | 36,000  | 39,249  | 33,300  |
| Škoda Yeti      |         |         |         |         | 11,018  | 52,604  | 70,300  | 90,952  | 82,400  |
| Škoda Rapid     |         |         |         |         |         |         | 1,700   | 9,292   | 103,800 |
| Škoda Citigo    |         |         |         |         |         |         | 509     | 36,687  | 45,200  |

Question: How many Skoda cars were sold in 2010?

Crucial Steps Selected:
Identify Objective: Define the goal.
Evidence Extraction:Extract relevant rows, columns, and text.
Python Code Generation: Generate single Python code to sum the extracted values.

Detailed Steps:

Identify Objective: Determine that the goal is to find the total number of Škoda cars sold in 2010.
Evidence Extraction: Extract the relevant data (the 2010 column) for all models listed in the table.
Python Code Generation: Generate Python code to sum the extracted values for the year 2010.

Example2:

Context:

The fair value of the Company's service-based RSUs was determined based on the fair market value of the Company's stock at the grant date, adjusted for dividends. The fair value of the Company's market-based PRSUs for fiscal years 2019, 2018, and 2017 was calculated using a Monte Carlo simulation model at the grant date. This model requires highly subjective inputs, such as expected stock price volatility and the estimated life of each award.

As of June 30, 2019, the Company had $271.9 million in total unrecognized compensation expense related to all unvested RSUs. This expense is expected to be recognized over a weighted-average remaining period of 2.2 years.

### Table: Key Assumptions for Fair Value Calculations of RSUs and PRSUs

| Metric                     | June 30, 2019 | June 24, 2018 | June 25, 2017 |
|----------------------------|---------------|---------------|---------------|
| Expected volatility         | 32.65%        | 34.07%        | 27.48%        |
| Risk-free interest rate      | 2.52%         | 2.35%         | 1.55%         |
| Expected term (years)       | 2.92          | 2.92          | 2.92          |
| Dividend yield              | 2.49%         | 1.05%         | 1.50%         |
	

Question: What is the amount of total unrecognised compensation expense as of June 30, 2019?

Crucial Steps Selected:
Identify Objective: Define the goal
Extract relevant information from the provided text.

Detailed Steps:
Identify Objective: The goal is to find the amount of total unrecognized compensation expense as of June 30, 2019.
Contextual Understanding: 
Recognize that the question refers to unrecognized compensation expense, which is detailed in the provided text, not in the table itself. The key phrase “As of June 30, 2019, the Company had $271.9 million of total unrecognized compensation expense” directly relates to the question.
Evidence Extraction: 
Focus on extracting the relevant value from the text portion, specifically the sentence: “As of June 30, 2019, the Company had $271.9 million of total unrecognized compensation expense.”
Direct Path to Answer: 
The extracted value from the text is the direct answer to the question.

Example3:

Table:
Note 13: Supplemental Balance Sheets and Statements of Operations Detail
(1) Fiscal year ended March 31, 2018 adjusted due to the adoption of ASC 606.

| | March 31, | |
| (amounts in thousands) | 2019 | 2018 |
| Accounts receivable: | | |
| Trade | $176,715 | $166,459 |
| Allowance for doubtful accounts reserve | (1,206) | (1,210) |
| Ship-from-stock and debit (“SFSD”) reserve | (18,862) | (17,362) |
| Returns reserves (1) | (964) | (131) |
| Rebates reserves | (967) | (446) |
| Price protection reserves | (657) | (420) |
| Other | — | (329) |
| Accounts receivable, net (1) | $154,059 | $146,561 |

Question: Which years does the table provide information for the Supplemental Balance Sheets and Statements of Operations Detail for the company?

Crucial Steps Selected:
Identify Objective: Define the goal.
Extract the years from the table's column headings.

Detailed Steps:
Identify Objective: The goal is to determine the years for which the table provides information regarding the Supplemental Balance Sheets and Statements of Operations Detail.
Evidence Extraction:
Focus on the table's column headings where the fiscal years are listed.
Identify any notes or footnotes that may provide additional context for the fiscal years (e.g., note indicating adjustments due to accounting changes).
Years Identification:
Extract the years mentioned in the column headers (2019 and 2018).
Review any footnotes like "(1) Fiscal year ended March 31, 2018 adjusted due to the adoption of ASC 606" to confirm if any additional context impacts the identification of years or data interpretation.
Direct Path to Answer: Confirm the years by directly referencing the extracted data from the tables column headings, ensuring alignment with any notes.

YourTask:
Comprehend the Crucial steps to Detailed Steps that are essential for solving the task for the provided table, text (if available) and question. Important - Do not answer the Question.

Tables: 
{table}

Question: {question}

{crucial_steps}

Detailed Steps:


"""

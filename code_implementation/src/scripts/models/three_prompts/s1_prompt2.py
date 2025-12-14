def get_s1_prompt(table, question, text=None):
    return f"""

You are a meta-selector tasked with constructing the most efficient pathway for solving tabular questions. Your goal is to select or create minimal, high-level steps to guide reasoning, avoiding direct answers. NOTE - Do not answer, only select crucial steps.

Guidelines:
Problem Understanding:
Identify Objective: Define the question's goal.
Comprehend Problem: Understand the scope and nature of the problem.

Reasoning Process:
Evidence Extraction: Extract relevant rows, columns, and text.
Decomposition: Break down complex questions into sub-questions if necessary.
Step-by-Step Reasoning: Apply logical steps to solve sub-questions or the main problem.
Python Code Generation: Opt to generate code (single or multiple scripts) if calculations are required.

Optimization Tips:
Direct Answer Path: Use evidence extraction to find the answer directly, when possible.
Simplify: Break down complex questions into simpler components.
Code Integration: Include Python code generation for essential calculations.

Few examples are given below with their respective crucial steps selected from the meta-reasoning process. Each example contains its own table, text, and question. Interpret the problem and select only the most essential steps for reaching to answer.

Examples:

Example1:
Table: 
  Model            | 2005   | 2006   | 2007   | 2008   | 2009   | 2010   | 2011   | 2012   | 2013   |
  Škoda Octavia    | 233322 | 270274 | 309951 | 344857 | 317335 | 349746 | 387200 | 409360 | 359600 |
  Škoda Fabia      | 236698 | 243982 | 232890 | 246561 | 264173 | 229045 | 266800 | 255025 | 202000 |
  Škoda Superb     | 22091  | 20989  | 20530  | 25645  | 44548  | 98873  | 116700 | 106847 | 94400  |
  Škoda Roomster   |       | 14422  | 66661  | 57467  | 47152  | 32332  | 36000  | 39249  | 33300  |
  Škoda Yeti       |       |       |       |       | 11018  | 52604  | 70300  | 90952  | 82400  |
  Škoda Rapid      |       |       |       |       |       |       | 1700   | 9292   | 103800 |
  Škoda Citigo     |       |       |       |       |       |       | 509    | 36687  | 45200  |

Question: How many Skoda cars were sold in 2010?

Crucial Steps Selected:

Identify Objective: Define the goal.
Evidence Extraction:Extract relevant rows, columns, and text.
Python Code Generation: Generate single Python code to sum the extracted values.

Example2:

Table:
The fair value of the Company's service-based RSUs was calculated based on fair market value of the Company's stock at the date of grant, discounted for dividends.
The fair value of the Company's market-based PRSUs granted during fiscal years 2019, 2018, and 2017 was calculated using a Monte Carlo simulation model at the date of the grant. This model requires the input of highly subjective assumptions, including expected stock price volatility and the estimated life of each award:
As of June 30, 2019, the Company had $271.9 million of total unrecognized compensation expense related to all unvested RSUs granted which is expected to be recognized over a weighted-average remaining period of 2.2 years.


|		|		|	YearEnded	|		|	
|		|	June 30, 2019	|	June 24, 2018	|	June 25, 2017	|	
|	Expected volatility	|	32.65%	|	34.07%	|	27.48%	|	
|	Risk-free interest rate	|	2.52%	|	2.35%	|	1.55%	|	
|	Expected term (years)	|	2.92	|	2.92	|	2.92	|	
|	Dividend yield	|	2.49%	|	1.05%	|	1.50%	|	
	

Question: What is the amount of total unrecognised compensation expense as of June 30, 2019?
Crucial Steps Selected:
Identify Objective: Define the goal
Extract relevant information from the provided text.


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


Your Task:
Select the Crucial steps that are essential for solving the task for the provided table, text (if available) and question, using the helpful tips. Important - Do not answer the Question, only select high level steps that are crucial for solving the tasks.


Tables: 
{table}

Question: {question}

Crucial Steps Selected:

"""

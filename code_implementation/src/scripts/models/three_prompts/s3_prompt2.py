def get_s3_prompt(table, question, detailed_steps, text):
    return f"""
You are responsible for delivering precise answers by strictly following the provided detailed steps. Each answer must be carefully reasoned, supported by clear explanations, and based on thorough analysis of the given table, text, and question.

Few examples are given below. Interpret the examples and understand the task to answer the tabular question according to the specific table, text, question by following the detailed steps to answer efficiently.

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

Detailed Steps:
Identify Objective: Determine that the goal is to find the total number of Škoda cars sold in 2010.
Evidence Extraction: Extract the relevant data (the 2010 column) for all models listed in the table.
Python Code Generation: Generate Python code to sum the extracted values for the year 2010.

Answer and Reasoning:
Identify Objective: The goal is to find the total number of Škoda cars sold in 2010.
2. Evidence Extraction: Extract the relevant data (the 2010 column) for all models listed in the table:
Škoda Octavia: 349746
Škoda Fabia: 229045
Škoda Superb: 98873
Škoda Roomster: 32332
Škoda Yeti: 52604
Škoda Rapid: N/A (No data for 2010)
Škoda Citigo: N/A (No data for 2010)
3. Python Code Generation: We can now sum the extracted values for the year 2010 using Python code
``` python ```
# Data for 2010
skoda_sales_2010 = [349746, 229045, 98873, 32332, 52604]

# Calculate the total sales for 2010
total_sales_2010 = sum(skoda_sales_2010)
print(f”Final Answer: {{total_sales_2010}}”)
#Done
```
4. Answer and Reasoning: Summing these values gives the total number of Škoda cars sold in 2010.
Final Answer: 762600

Example2:
Table:
The fair value of the Companys service-based RSUs was calculated based on fair market value of the Companys stock at the date of grant, discounted for dividends.
The fair value of the Companys market-based PRSUs granted during fiscal years 2019, 2018, and 2017 was calculated using a Monte Carlo simulation model at the date of the grant. This model requires the input of highly subjective assumptions, including expected stock price volatility and the estimated life of each award:
As of June 30, 2019, the Company had $271.9 million of total unrecognized compensation expense related to all unvested RSUs granted which is expected to be recognized over a weighted-average remaining period of 2.2 years.


|		|		|	YearEnded	|		|	
|		|	June 30, 2019	|	June 24, 2018	|	June 25, 2017	|	
|	Expected volatility	|	32.65%	|	34.07%	|	27.48%	|	
|	Risk-free interest rate	|	2.52%	|	2.35%	|	1.55%	|	
|	Expected term (years)	|	2.92	|	2.92	|	2.92	|	
|	Dividend yield	|	2.49%	|	1.05%	|	1.50%	|	
	

Question: What is the amount of total unrecognised compensation expense as of June 30, 2019?

Detailed Steps:
Identify Objective: The goal is to find the amount of total unrecognized compensation expense as of June 30, 2019.
Contextual Understanding: 
Recognize that the question refers to unrecognized compensation expense, which is detailed in the provided text, not in the table itself. The key phrase “As of June 30, 2019, the Company had $271.9 million of total unrecognized compensation expense” directly relates to the question.
Evidence Extraction: 
Focus on extracting the relevant value from the text portion, specifically the sentence: “As of June 30, 2019, the Company had $271.9 million of total unrecognized compensation expense.”
Direct Path to Answer: 
The extracted value from the text is the direct answer to the question.

Answer && Reasoning:
Identify Objective: The goal is to find the amount of total unrecognized compensation expense as of June 30, 2019.
Contextual Understanding: The question refers to the unrecognized compensation expense, which is explicitly detailed in the provided text. It is not found in the table but is given as part of the explanatory information.
Evidence Extraction: From the provided text, the key sentence reads: "As of June 30, 2019, the Company had $271.9 million of total unrecognized compensation expense."
Direct Path to Answer: The extracted value from the text is the answer to the question. The total unrecognized compensation expense as of June 30, 2019, is $271.9 million.
Answer and Reasoning: By focusing on the relevant part of the text, we can directly conclude that the total unrecognized compensation expense is $271.9 million as of June 30, 2019.
Final Answer: $271.9 million.

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

Detailed Steps:
Identify Objective: The goal is to determine the years for which the table provides information regarding the Supplemental Balance Sheets and Statements of Operations Detail.

Evidence Extraction:
Focus on the table's column headings where the fiscal years are listed.
Identify any notes or footnotes that may provide additional context for the fiscal years (e.g., note indicating adjustments due to accounting changes).

Years Identification:
Extract the years mentioned in the column headers (2019 and 2018).
Review any footnotes like "(1) Fiscal year ended March 31, 2018 adjusted due to the adoption of ASC 606" to confirm if any additional context impacts the identification of years or data interpretation.

Direct Path to Answer: Confirm the years by directly referencing the extracted data from the table's column headings, ensuring alignment with any notes.

Answer && Reasoning:
Identify Objective: The goal is to determine the years for which the table provides information about the Supplemental Balance Sheets and Statements of Operations Detail for the company.
Evidence Extraction:
From the table, focus on the column headings to identify the fiscal years being referenced.
The table columns list the following fiscal years: 2019 and 2018.
A footnote "(1) Fiscal year ended March 31, 2018 adjusted due to the adoption of ASC 606" provides additional context, indicating that 2018 was adjusted due to a change in accounting standards (ASC 606).
Direct Path to Answer: The years for which the table provides information are 2019 and 2018, with the fiscal year ending March 31, 2018, being adjusted according to the footnote.
Answer and Reasoning: The table provides information for the fiscal years 2019 and 2018. The 2018 data was adjusted due to the adoption of ASC 606, as noted in the footnote.
Final Answer: The years are 2019 and 2018.


Your Task:
Answer the question based on provided tables and text (if available) by following the given detailed steps. Conclude with a final answer, in case of multiple answers, return a list of answers.

Tables: 
{table}

Question: {question}

{detailed_steps}

Answer && Reasoning:

"""

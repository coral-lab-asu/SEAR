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

### Total Domestic Business R&D and Software R&D Expenditures: 2006 and 2016

| Year and Industry     | Total Business R&D (in million $) | Software R&D (in million $) |
|-----------------------|-----------------------------------|-----------------------------|
| **2006**              |                                   |                             |
| All industries        | 247,669                           | 48,299                      |
| Manufacturing         | 171,814                           | 10,720                      |
| Nonmanufacturing       | 75,855                            | 37,579                      |
| **2016**              |                                   |                             |
| All industries        | 374,685                           | 120,824                     |
| Manufacturing         | 250,553                           | 35,984                      |
| Nonmanufacturing       | 124,132                           | 84,840                      |
| **2006-16 Annual Growth Rate (%)** |                        |                             |
| All industries        | 4.2%                              | 9.6%                        |
| Manufacturing         | 3.8%                              | 12.9%                       |
| Nonmanufacturing       | 5.0%                              | 8.5%                        |

Question: how many million dollars did for-profit businesses perform in software r&d in 2016?

Crucial Steps Selected:
Identify Objective: Define the goal.
Evidence Extraction: Extract relevant rows, columns, and text.
Direct Answer Path: Use evidence extraction to answer directly from the table.

Detailed Steps:

Identify Objective: Understand that the question asks for the amount of money (in million dollars) that for-profit businesses spent on software R&D in 2016.
Evidence Extraction: Identify the row labeled "2016" and the column labeled "software r&d" in the table. Focus specifically on the "software r&d" value for all industries, as this represents the total amount spent on software R&D by for-profit businesses in 2016.
Direct Answer Path: Answer directly from the table the extracted value from the intersection of the 2016 row and the software R&D column is the answer to the question. Since the question is about for-profit businesses and the table represents industry expenditures, this value can be directly used as the answer.

Example3:
Context:

### Table 0: Benefit Plan Contributions (2015-2017)

| Benefit Plan            | 2017   | 2016   | 2015   |
|-------------------------|--------|--------|--------|
| Pension Plan            | $3,856 | $3,979 | $2,732 |
| Health Plan             | 11,426 | 11,530 | 8,736  |
| Other Plans             | 1,463  | 1,583  | 5,716  |
| **Total Plan Contributions** | $16,745 | $17,092 | $17,184 |

---

### Table 1: Loan and Financial Obligations by Year

|                          | 2018    | 2019    | 2020    | 2021    | 2022    | Thereafter | Total       |
|--------------------------|---------|---------|---------|---------|---------|------------|-------------|
| Property Mortgages and Other Loans | $153,593 | $42,289  | $703,018 | $11,656  | $208,003 | $1,656,623  | $2,775,182  |
| MRA Facilities           | $90,809 | —       | —       | —       | —       | —          | $90,809     |
| Revolving Credit Facility | —       | —       | —       | —       | —       | $40,000    | $40,000     |
| Unsecured Term Loans     | —       | —       | —       | —       | —       | $1,500,000 | $1,500,000  |
| Senior Unsecured Notes   | $250,000 | —       | $250,000 | —       | $800,000 | $100,000  | $1,400,000  |
| Trust Preferred Securities | —       | —       | —       | —       | —       | $100,000  | $100,000    |
| Capital Lease            | $2,387  | $2,411  | $2,620  | $2,794  | $2,794  | $819,894   | $832,900    |
| Ground Leases            | $31,049 | $31,066 | $31,436 | $31,628 | $29,472 | $703,254   | $857,905    |


Question: What is the sum of Ground leases of 2020, Health Plan of 2016, and Property mortgages and other loans of Thereafter ?

Crucial Steps Selected:
Identify Objective: Define the goal.
Evidence Extraction: Extract relevant rows, columns, and text from both tables.
Python Code Generation: Generate a single Python script to sum the extracted values.

Detailed Steps:

Identify Objective: The task is to find the sum of three values: Ground leases from 2020, the Health Plan from 2016, and Property mortgages and other loans from the "Thereafter" column.
Evidence Extraction: 
Table 0 Extraction: Locate the row labeled "Health Plan" in Table 0. Extract the value from the 2016 column corresponding to the Health Plan row.
Table 1 Extraction: Locate the row labeled "Ground leases" in Table 1. Extract the value from the 2020 column corresponding to Ground leases. Locate the row labeled "Property mortgages and other loans" in Table 1. Extract the value from the "Thereafter" column corresponding to Property mortgages and other loans.
Data Aggregation or Calculation: Since the task involves summing the three extracted values,
1.  Ground leases value from 2020
2.  Health Plan value from 2016
3.  Property mortgages and other loans value from Thereafter

generate a Python code to sum these values, ensure that the extracted values are in a format that allows for numeric summation (removing dollar signs and commas if necessary).

YourTask:
Comprehend the Crucial steps to Detailed Steps that are essential for solving the task for the provided table, text (if available) and question. Important - Do not answer the Question.

Tables: 
{table}

Question: {question}

{crucial_steps}

Detailed Steps:


"""

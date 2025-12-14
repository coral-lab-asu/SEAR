def get_s3_prompt(table, question, detailed_steps, text):
    return f"""
You are responsible for delivering precise answers by strictly following the provided detailed steps. Each answer must be carefully reasoned, supported by clear explanations, and based on thorough analysis of the given table, text, and question.

Few examples are given below. Interpret the examples and understand the task to answer the tabular question according to the specific table, text, question by following the detailed steps to answer efficiently.

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

Detailed Steps:
Identify Objective: Understand that the question asks for the amount of money (in million dollars) that for-profit businesses spent on software R&D in 2016.
Evidence Extraction: Identify the row labeled "2016" and the column labeled "software r&d" in the table. Focus specifically on the "software r&d" value for all industries, as this represents the total amount spent on software R&D by for-profit businesses in 2016.
Direct Answer Path: Answer directly from the table the extracted value from the intersection of the 2016 row and the software R&D column is the answer to the question. Since the question is about for-profit businesses and the table represents industry expenditures, this value can be directly used as the answer.

Answer and Reasoning:
Identify Objective: The goal is to find the total amount of money (in million dollars) that for-profit businesses spent on software R&D in 2016.
Evidence Extraction: From the provided table, focus on the row for "2016" and the column for "software r&d."
The value at the intersection of the 2016 row and the software R&D column for "all industries" is 120824 million dollars.
Direct Answer Path: The question asks for the total software R&D performed by for-profit businesses, which is already captured by the value for "all industries" in the table.
Answer and Reasoning: The amount of money spent by for-profit businesses on software R&D in 2016 is 120824 million dollars. This figure represents the total software R&D expenditure across all industries, as indicated by the table.
Final Answer: 120824 million dollars.

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

Answer && Reasoning:

Identify Objective:
The task is to find the sum of three specific values:
Ground leases for 2020
Health Plan for 2016
Property mortgages and other loans for "Thereafter"
Evidence Extraction:

Ground leases (2020): From Table 1, locate the "Ground leases" row, and extract the value from the 2020 column:
Value = 31,436
Health Plan (2016): From Table 0, locate the "Health Plan" row, and extract the value from the 2016 column:
Value = 11,530
Property mortgages and other loans (Thereafter): From Table 1, locate the "Property mortgages and other loans" row, and extract the value from the "Thereafter" column:
Value = 1,656,623

Data Aggregation or Calculation:
Now, we will sum the three extracted values.
Python Code to Sum the Values:

```python```
# Data from the table (remove commas)
ground_leases_2020 = 31436
health_plan_2016 = 11530
property_mortgages_thereafter = 1656623

# Sum the values
total_sum = ground_leases_2020 + health_plan_2016 + property_mortgages_thereafter
print(f"Final Answer: {{total_sum}}")

#Done
```

Answer and Reasoning:
By summing the values:
Ground leases (2020): 31,436
Health Plan (2016): 11,530
Property mortgages and other loans (Thereafter): 1,656,623
The total sum is 1,699,589.
Final Answer:
The sum of Ground leases from 2020, Health Plan from 2016, and Property mortgages and other loans from the "Thereafter" column is 1,699,589.

Your Task:
Answer the question based on provided tables and text (if available) by following the given detailed steps. Conclude with a final answer, in case of multiple answers, return a list of answers.

Tables: 
{table}

Question: {question}

{detailed_steps}

Answer && Reasoning:

"""

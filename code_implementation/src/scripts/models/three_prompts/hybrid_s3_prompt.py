def get_s3_prompt(table, question, detailed_steps, text):
    return f"""
You are responsible for delivering precise answers by strictly following the provided detailed steps. Each answer must be carefully reasoned, supported by clear explanations, and based on thorough analysis of the given table, more context, and question.

Few examples are given below. Interpret the examples and understand the task to answer the tabular question according to the specific table, text, question by following the detailed steps to answer efficiently.

Examples:

Example1:
Table Title: Player Statistics  
Table Subtitle: Career highlights of players

Table:
No | Player         | Position | Career     | Date honored
-- | -------------  | -------- | ---------- | -------------
7  | Keith Tkachuk  | C        | 1992-2001  | December 23, 2011
19  | Bobby Hull     | LW       | 1972-1980  | February 19, 1989
19 | Shane Doan     | RW       | 1996-2017  | February 24, 2019

More context:
- Keith Tkachuk (USA) is an American former professional ice hockey player who played in the NHL in an 18-year career with the Winnipeg Jets, Phoenix Coyotes, St. Louis Blues, and Atlanta Thrashers, retiring in 2010. He is considered one of the greatest U.S.-born players in NHL history.
- Bobby Hull (CAN) is a Canadian former ice hockey player who is regarded as one of the greatest players of all time, known for his blonde hair and legendary skating speed.
- Shane Doan (CAN) is a Canadian former professional ice hockey forward who spent the entirety of his NHL career with the Winnipeg Jets/Arizona Coyotes franchise, retiring in 2017. He was the longest-serving NHL captain at the time of his retirement.

Question: Arizona Coyotes player number 19 played in how many NHL seasons?

Detailed Steps:
Identify Objective: Determine the number of NHL seasons played by the Arizona Coyotes player wearing jersey number 19.  
Evidence Extraction: Find the row where jersey number is 19, extract the "Career" column, and verify the player's timeline.  
Decomposition:  
- Identify the career start and end years.  
- Compute the total seasons played, including both years.  
Python Code Generation: Generate a script to calculate the total seasons using the extracted career data.


Answer && Reasoning:
Identify Objective: Determine the goal: Calculate the number of NHL seasons played by the Arizona Coyotes player with jersey number 19.

Evidence Extraction:
From the table:
- Player with jersey number 19 is Shane Doan.
- His "Career" column shows: 1996-2017.

From the additional context:
- Shane Doan spent his entire NHL career with the Winnipeg Jets/Arizona Coyotes franchise, confirming his affiliation with the Arizona Coyotes.
- His career start and end years align with the "Career" column in the table.

Decomposition:
To calculate the number of seasons played:
- Identify the start year (1996) and the end year (2017) from the "Career" column.
- Compute the total seasons by including both start and end years: \( \text{{End Year}} - \text{{Start Year}} + 1 \).

Python Code Generation:

```python
# Career start and end years
start_year = 1996
end_year = 2017

# Calculate the total number of seasons
total_seasons = end_year - start_year + 1
print(f"Total NHL Seasons Played: {{total_seasons}}")
```

Answer and Reasoning:
- Start year: 1996.
- End year: 2017.
- Total seasons: 2017 - 1996 + 1 = 22.

Final Answer: Shane Doan, wearing jersey number 19, played 22 NHL seasons.

Example2:

Table Title: Ice Cream Sales  
Table Subtitle: Sales data for different ice cream flavors

Table:
Flavor   | Sales
-------- | -----
Vanilla  | 1500
Chocolate| 1200
Strawberry | 900

More context:
- The ice cream sales data was collected over the summer season.
- Vanilla has been the most popular flavor for several years.
- Chocolate and Strawberry flavors also have a consistent customer base.

Question: What is the total sales of all ice cream flavors?

Detailed Steps:
Identify Objective: Compute the total sales of all ice cream flavors listed in the table.  
Evidence Extraction: Extract the "Sales" column for Vanilla, Chocolate, and Strawberry, ensuring completeness.  
Decomposition:  
- Retrieve sales values for all listed flavors.  
- Sum the sales amounts.  
- Validate extracted data for accuracy.  
Validation: Verify sales values are correctly recorded and ensure no missing data.  
Python Code Generation: Generate a script to read sales values and compute the total efficiently.

Answer && Reasoning:
Identify Objective: The goal is to compute the total sales of all the listed ice cream flavors: Vanilla, Chocolate, and Strawberry.

Evidence Extraction:
From the table:
- Sales for Vanilla: 1500.
- Sales for Chocolate: 1200.
- Sales for Strawberry: 900.

Decomposition:
To calculate the total sales:
1. Extract the sales values for each flavor.
2. Sum the values: \( 1500 + 1200 + 900 \).

Validation:
- All sales values are directly extracted from the table and are accurate.
- No additional context or hidden rows suggest any adjustments are needed.

Python Code Generation:
Here is the Python code to calculate the total sales:

```python
# Sales data for each flavor
sales = {{
    "Vanilla": 1500,
    "Chocolate": 1200,
    "Strawberry": 900
}}

# Calculate total sales
total_sales = sum(sales.values())
print(f"Total Ice Cream Sales: {{total_sales}}")
```

Execution of the Calculation:
Perform the summation: 1500 + 1200 + 900 = 3600

Final Answer:
The total sales of all ice cream flavors are 3600.

Your Task:
Answer the question based on provided tables and more context by following the given detailed steps. Conclude with a final answer, in case of multiple answers, return a list of answers.


Tables: 
{table}

Question: {question}

{detailed_steps}

Answer && Reasoning:

"""

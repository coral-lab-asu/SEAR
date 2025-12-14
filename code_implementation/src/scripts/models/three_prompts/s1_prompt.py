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
Title : total domestic business r&d and software r&d expenditures: 2006 and 2016
|	year and industry	|	total business r&d	|	software r&d	|	
|	2006	|		|		|	
|	all industries	|	247669	|	48299	|	
|	manufacturing	|	171814	|	10720	|	
|	nonmanufacturing	|	75855	|	37579	|	
|	2016	|		|		|	
|	all industries	|	374685	|	120824	|	
|	manufacturing	|	250553	|	35984	|	
|	nonmanufacturing	|	124132	|	84840	|	
|	2006-16 annual growth rate (%)a	|		|		|	
|	all industries	|	4.2	|	9.6	|	
|	manufacturing	|	3.8	|	12.9	|	
|	nonmanufacturing	|	5	|	8.5	|	

Question: how many million dollars did for-profit businesses perform in software r&d in 2016?

Crucial Steps Selected:

Identify Objective: Define the goal.
Evidence Extraction: Extract relevant rows, columns, and text.
Direct Answer Path: Use evidence extraction to answer directly from the table.

Example3:

Tables:
 Table_0
 Benefit Plan	|	2017	|	2016	|	2015	|	
 Pension Plan	|	$3,856	|	$3,979	|	$2,732	|	
 Health Plan	|	11426	|	11530	|	8736	|	
 Other plans	|	1463	|	1583	|	5716	|	
 Total plan contributions	|	$16,745	|	$17,092	|	$17,184	|	


 Table_1
 |		|	2018	|	2019	|	2020	|	2021	|	2022	|	Thereafter	|	Total	|	
 |	Property mortgages and other loans	|	$153,593	|	$42,289	|	$703,018	|	$11,656	|	$208,003	|	$1,656,623	|	$2,775,182	|	
 |	MRA facilities	|	90809	|	—	|	—	|	—	|	—	|	—	|	90809	|	
 |	Revolving credit facility	|	—	|	—	|	—	|	—	|	—	|	40000	|	40000	|	
 |	Unsecured term loans	|	—	|	—	|	—	|	—	|	—	|	1500000	|	1500000	|	
 |	Senior unsecured notes	|	250000	|	—	|	250000	|	—	|	800000	|	100000	|	1400000	|	
 |	Trust preferred securities	|	—	|	—	|	—	|	—	|	—	|	100000	|	100000	|	
 |	Capital lease	|	2387	|	2411	|	2620	|	2794	|	2794	|	819894	|	832900	|	
 |	Ground leases	|	31049	|	31066	|	31436	|	31628	|	29472	|	703254	|	857905	|



Question: What is the sum of Ground leases of 2020, Health Plan of 2016, and Property mortgages and other loans of Thereafter ?

Crucial Steps Selected:

Identify Objective: Define the goal.
Evidence Extraction: Extract relevant rows, columns, and text from both tables.
Python Code Generation: Generate a single Python script to sum the extracted values.

Your Task:
Select the Crucial steps that are essential for solving the task for the provided table, text (if available) and question, using the helpful tips. Important - Do not answer the Question, only select high level steps that are crucial for solving the tasks.


Tables: 
{table}

Question: {question}

Crucial Steps Selected:


"""

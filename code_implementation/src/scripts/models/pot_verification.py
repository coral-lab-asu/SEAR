# Python
def finqa0():

    # Define closing prices for Citi common stock
    citi_prices = {
        "2012-12-31": 100.0,
        "2013-12-31": 131.8,
        "2014-12-31": 137.0,
        "2015-12-31": 131.4,
        "2016-12-31": 152.3,
        "2017-12-31": 193.5
    }

    # Target date (end of the five-year period)
    target_date = "2017-12-31"

    # Starting price (first year)
    start_price = citi_prices["2012-12-31"]

    # Ending price (target date)
    end_price = citi_prices[target_date]

    # Calculate cumulative return
    cumulative_return = ((end_price - start_price) / start_price) * 100

    # Convert return to percentage and format string with two decimal places
    percentage_return = "{:.2f}".format(cumulative_return)

    # Answer string
    answer = f'''Percentage cumulative total return for Citi common stock for the five-year period ended December 31, 2017: {percentage_return}%'''

    print(answer)

def finqa1():
    # Python

    # Extract data from the context
    available_for_sale_investment = 14001  # in millions
    total_cash_and_investment = 26302  # in millions

    # Calculate the percentage
    percent_available_for_sale_investment = (available_for_sale_investment / total_cash_and_investment) * 100

    # Format the answer as a string
    answer = f'''Percentage of total cash and investments comprised of available-for-sale investments: {percent_available_for_sale_investment:.2f}%'''

    print(answer)

#finqa1()

def fetaqa0():
    # 1. Identify the column that contains the discounted R for year 2. (independent, support=[Year --> | 1 | 2 | 3 | 4 | 5, Sales | 700 | 900 | 1200 | 1600 | 2200, OPR | 75 | 105 | 130 | 200 | 280, Royalty | 60 | 36 | 48 | 64 | 88, Discount Factor,10% | 0.9091 | 0.8264 | 0.7531 | 0.6830 | 0.6209, Discounted OPR | 68.2 | 86.8 | 97.7 | 136.6 | 173.9, Discounted R | 54.5 | 29.8 | 36.1 | 43.7 | 54.6])
    discounted_R_year2 = 29.8
    # 2. Identify the column that contains the discounted R for year 1. (independent, support=[Year --> | 1 | 2 | 3 | 4 | 5, Sales | 700 | 900 | 1200 | 1600 | 2200, OPR | 75 | 105 | 130 | 200 | 280, Royalty | 60 | 36 | 48 | 64 | 88, Discount Factor,10% | 0.9091 | 0.8264 | 0.7531 | 0.6830 | 0.6209, Discounted OPR | 68.2 | 86.8 | 97.7 | 136.6 | 173.9, Discounted R | 54.5 | 29.8 | 36.1 | 43.7 | 54.6])
    discounted_R_year1 = 54.5
    # 3. Sum up the discounted R for year 1 and year 2. (depends on 1 and 2, support=[])
    present_value_2_years = discounted_R_year1 + discounted_R_year2
    print(present_value_2_years)

#fetaqa0()

# # Define the table including the header
# table = [
#   [""Party"", ""Party"", ""Candidate"", ""Votes"", ""%"", ""±""],
#   [""-"", ""Irish Unionist"", ""Robert McCalmont"", 15,206, 94.6, ""N/A""],
#   [""-"", ""Sinn Féin"", ""Daniel Dumigan"", 861, 5.4, ""N/A""],
#   [""Majority"", ""Majority"", ""Majority"", 14,345, 89.3, ""N/A""],
#   [""Turnout"", ""Turnout"", ""Turnout"", 16,067, 64.8, ""N/A""],
#   [""Registered electors"", ""Registered electors"", ""Registered electors"", 24,798, ""-"", ""-""],
#   [""-"", ""Irish Unionist hold"", ""Irish Unionist hold"", ""Swing"", ""-"", ""-""]
# ]

# # Find the performance of the Unionist Candidate
# unionist_performance = [row for row in table if ""Irish Unionist"" in row[1]]

# # Save the result in the ans variable
# ans = unionist_performance

# # Print the ans
# print(ans)
# # Done

# table = [
#     ["Title", "Year", "Role", "Notes"],
#     ["Wilmot", "1999", "Wilmot Tanner", "Main role"],
#     ["Where the Heart Is", "2000–06", "Luke Kirkwall", "68 episodes"],
#     ["Casualty", "2002", "Mark Booth", "\"Only The Lonely\""],
#     ["Barking!", "2004", "Ryan", "\"The Big Sausage\""],
#     ["Doctors", "2006", "Gary", "\"Positively Blooming\""],
#     ["Casualty", "2006", "Jude Becket", "\"Sons & Lovers\""],
#     ["Inspector George Gently", "2007", "Billy Lister", "\"Gently Go Man\""],
#     ["The Chase", "2007", "Liam Higgins", "9 episodes"],
#     ["The Royal", "2007", "Bobby Horrocks", "\"Starting Over\""],
#     ["Robin Hood", "2007", "Luke Scarlett", "\"The Angel of Death\""],
#     ["Echo Beach", "2008", "Brae Marrack", "Main role"],
#     ["Moving Wallpaper", "2008", "Himself", "3 episodes"],
#     ["Moving Wallpaper: The Mole", "2008", "Himself", "Webisode; Episode 1.4"],
#     ["Doctor Who", "2008", "Ross Jenkins", "\"The Sontaran Stratagem\", \"The Poison Sky\""],
#     ["Demons", "2009", "Luke Rutherford-Van Helsing", "Main role"],
#     ["Trinity", "2009", "Lord Dorian Gaudain", "Main role"],
#     ["Dark Relic", "2010", "Paul", "Television film"],
#     ["The Promise", "2011", "Sergeant Leonard Matthews", "Miniseries"],
#     ["Magic City", "2012–13", "Danny Evans", "Main role"],
#     ["Witches of East End", "2014", "Frederick Beauchamp", "Main role; Season 2"],
#     ["Stonemouth", "2015", "Stewart Gilmour", "Main role"],
#     ["The Art of More", "2015–16", "Graham Connor", "Main role"],
#     ["Ordeal by Innocence", "2018", "Mickey Argyll", "BBC Television film (Replacing Ed Westwick)"]
# ]

# roles_2009 = [row[2] for row in table if row[1] == "2009"]
# ans = roles_2009

# print(ans)

cash_flow_hedge_2011 = -4614
cash_flow_hedge_2010 = 2014

# Program of Thought
percentage_change = ((cash_flow_hedge_2011 - cash_flow_hedge_2010) / cash_flow_hedge_2010) * 100

print(f"The percentage change in cash flow hedges in 2011 compared to 2010 is {percentage_change:.2f}%")

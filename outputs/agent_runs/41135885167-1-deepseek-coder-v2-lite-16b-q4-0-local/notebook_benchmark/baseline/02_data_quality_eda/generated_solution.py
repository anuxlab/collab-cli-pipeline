import pandas as pd

# Construct DataFrame
data = {
    'date': ['2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01', '2022-06-01', '2022-07-01', '2022-08-01', '2022-09-01', '2022-10-01', '2022-11-01', '2022-12-01'],
    'region': ['East', 'West', 'North', 'South', 'East', 'West', 'North', 'South', 'East', 'West', 'North', 'South'],
    'product': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
    'units': [100, 200, 150, 250, 120, None, 130, 220, 110, 210, 140, 230],
    'unit_price': [10, 15, 12, 18, 11, 16, 13, 19, 10, 17, 12, 19],
    'customer_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
}

df = pd.DataFrame(data)

# Check for missing values
missing_values = df.isna().sum()
print("Missing values in each column:\n", missing_values)

# Check for duplicates
duplicates = df.duplicated().sum()
print("Number of duplicate rows:\n", duplicates)

# Group by region and calculate summary statistics
region_summary = df.groupby('region').agg({'units': ['mean', 'sum', 'count'], 'unit_price': ['mean', 'sum', 'count']})
print("Summary statistics grouped by region:\n", region_summary)

# Describe the DataFrame
description = df.describe()
print("Descriptive statistics of the DataFrame:\n", description)

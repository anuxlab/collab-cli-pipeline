import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Task ID
task_id = "retail_transactions_analysis"

# Create a DataFrame with intentional missing values and duplicates
data = {
    'date': pd.to_datetime(['2023-01-01', '2023-01-01', '2023-01-02', '2023-01-03', '2023-01-03', '2023-01-04', '2023-01-04', '2023-01-04', '2023-01-05', '2023-01-05', '2023-01-05', '2023-01-05']),
    'region': ['North', 'North', 'South', 'South', 'South', 'East', 'East', 'East', 'West', 'West', 'West', np.nan],
    'product': ['A', 'B', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'C', 'A'],
    'units': [10, 20, 15, 25, 30, 10, 20, 15, 10, 20, 15, 10],
    'unit_price': [10.0, 15.0, 12.0, 18.0, 20.0, 10.0, 15.0, 12.0, 10.0, 15.0, 12.0, 10.0],
    'customer_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
}

df = pd.DataFrame(data)

# Audit missingness and duplicates
missing_before = df.isnull().sum().sum()
duplicates_before = df.duplicated().sum()

# Clean the data
df.dropna(inplace=True)  # Drop rows with missing values
df.drop_duplicates(inplace=True)  # Drop duplicate rows

# Engineer revenue
df['revenue'] = df['units'] * df['unit_price']

# Groupby revenue by region and monthly trend
grouped = df.groupby([df['date'].dt.to_period('M'), 'region'])['revenue'].sum().unstack(fill_value=0)

# Create plots
fig, axes = plt.subplots(1, 2, figsize=(12, 6))

# Plot 1: Monthly revenue by region
grouped.plot(kind='bar', ax=axes[0], stacked=True)
axes[0].set_title('Monthly Revenue by Region')
axes[0].set_xlabel('Month')
axes[0].set_ylabel('Revenue')

# Plot 2: Summary statistics
df.describe(include='all').plot(kind='bar', ax=axes[1])
axes[1].set_title('Summary Statistics')
axes[1].set_xlabel('Columns')
axes[1].set_ylabel('Values')

# Save plots
plt.savefig('plots.png')

# Print benchmark result
BENCHMARK_RESULT = {
    "task_id": task_id,
    "rows_before": len(data),
    "rows_after": len(df),
    "missing_before": missing_before,
    "duplicates_before": duplicates_before,
    "total_revenue": grouped.sum().sum(),
    "regions": list(grouped.columns)
}

print(BENCHMARK_RESULT)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

# Set seed for reproducibility
np.random.seed(42)

# Create a sample DataFrame
data = {
    'date': pd.date_range(start='1/1/2022', periods=12, freq='M'),
    'region': np.random.choice(['North', 'South', 'East', 'West'], 12),
    'product': np.random.choice(['Product A', 'Product B', 'Product C'], 12),
    'units': np.random.randint(1, 100, 12),
    'unit_price': np.random.uniform(10, 100, 12),
    'customer_id': np.random.randint(1000, 10000, 12)
}

# Intentionally add a missing value and a duplicate
data['units'][5] = np.nan
data['date'][10] = data['date'][9]  # Duplicate date

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
grouped = df.groupby(['region', df['date'].dt.to_period('M')]).sum().reset_index()

# Create plots
fig, axes = plt.subplots(2, 1, figsize=(10, 10))

# Plot 1: Total revenue by region
grouped.pivot(index='date', columns='region', values='revenue').plot(ax=axes[0], kind='bar', stacked=True)
axes[0].set_title('Total Revenue by Region Over Time')
axes[0].set_xlabel('Month')
axes[0].set_ylabel('Revenue')

# Plot 2: Monthly trend of revenue
grouped.pivot(index='date', columns='region', values='revenue').plot(ax=axes[1], kind='line')
axes[1].set_title('Monthly Trend of Revenue by Region')
axes[1].set_xlabel('Month')
axes[1].set_ylabel('Revenue')

plt.tight_layout()
plt.savefig('revenue_plots.png')

# Assertions and interpretation
assert len(df) == 10, "Data cleaning did not remove the correct number of rows."
assert df.isnull().sum().sum() == 0, "There are still missing values in the DataFrame."
assert df.duplicated().sum() == 0, "There are still duplicate rows in the DataFrame."

# Calculate total revenue and regions
total_revenue = df['revenue'].sum()
regions = df['region'].unique().tolist()

# Prepare the result
result = {
    "task_id": "retail_transactions_analysis",
    "rows_before": 12,
    "rows_after": len(df),
    "missing_before": missing_before,
    "duplicates_before": duplicates_before,
    "total_revenue": total_revenue,
    "regions": regions
}

print("BENCHMARK_RESULT=" + json.dumps(result))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set seed for reproducibility
np.random.seed(42)

# Create a DataFrame with intentional missing values and duplicates
data = {
    'date': pd.date_range(start='1/1/2023', periods=12, freq='M'),
    'region': np.random.choice(['North', 'South', 'East', 'West'], 12),
    'product': np.random.choice(['Product A', 'Product B', 'Product C'], 12),
    'units': np.random.randint(1, 100, 12),
    'unit_price': np.random.uniform(10, 100, 12),
    'customer_id': np.random.randint(1000, 10000, 12)
}

# Intentionally add a missing value and a duplicate
data['units'][5] = np.nan
data['date'][10] = data['date'][0]  # Duplicate date

df = pd.DataFrame(data)

# Audit missingness and duplicates
missing_before = df.isnull().sum().sum()
duplicates_before = df.duplicated().sum()

# Clean the data
df.drop_duplicates(inplace=True)
df.dropna(inplace=True)

# Engineer revenue
df['revenue'] = df['units'] * df['unit_price']

# Groupby revenue by region and monthly trend
grouped = df.groupby([df['date'].dt.to_period('M'), 'region']).sum().reset_index()

# Create plots
fig, axes = plt.subplots(2, 1, figsize=(10, 12))

# Plot 1: Monthly revenue by region
grouped.pivot(index='date', columns='region', values='revenue').plot(ax=axes[0], kind='line')
axes[0].set_title('Monthly Revenue by Region')
axes[0].set_xlabel('Month')
axes[0].set_ylabel('Revenue')

# Plot 2: Total revenue by region
grouped.groupby('region')['revenue'].sum().plot(ax=axes[1], kind='bar')
axes[1].set_title('Total Revenue by Region')
axes[1].set_xlabel('Region')
axes[1].set_ylabel('Revenue')

# Save plots
plt.savefig('monthly_revenue.png')
plt.savefig('total_revenue.png')

# Assertions and interpretation
assert df.shape[0] == 10, "There should be 10 rows after cleaning."
assert df.isnull().sum().sum() == 0, "There should be no missing values after cleaning."
assert df.duplicated().sum() == 0, "There should be no duplicates after cleaning."
assert df['revenue'].sum() == grouped['revenue'].sum(), "Total revenue should match."

# Calculate total revenue and regions
total_revenue = df['revenue'].sum()
regions = df['region'].unique()

# Print benchmark result
BENCHMARK_RESULT = {
    "task_id": "retail_transactions_analysis",
    "rows_before": 12,
    "rows_after": 10,
    "missing_before": missing_before,
    "duplicates_before": duplicates_before,
    "total_revenue": total_revenue,
    "regions": regions.tolist()
}

print(BENCHMARK_RESULT)

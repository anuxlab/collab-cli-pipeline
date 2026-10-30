import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Construct DataFrame
data = {
    'date': pd.date_range(start='2023-01-01', periods=12, freq='M').tolist() * 2,
    'region': ['North', 'South'] * 6,
    'product': ['A', 'B', 'C', 'D', 'E', 'F'] * 2,
    'units': np.random.randint(1, 100, size=24),
    'unit_price': np.random.uniform(10, 100, size=24),
    'customer_id': np.random.randint(1000, 2000, size=24)
}

# Intentionally introduce a missing value and a duplicate
data['units'][5] = np.nan  # Missing value
data['customer_id'][10] = data['customer_id'][9]  # Duplicate

df = pd.DataFrame(data)

# Audit missingness and duplicates
rows_before = len(df)
missing_before = df.isna().sum().sum()
duplicates_before = df.duplicated().sum()

# Clean missingness and duplicates
df_cleaned = df.dropna().drop_duplicates()

# Engineer revenue
df_cleaned['revenue'] = df_cleaned['units'] * df_cleaned['unit_price']

# Groupby revenue by region and monthly trend
revenue_by_region = df_cleaned.groupby(['region', pd.Grouper(key='date', freq='M')])['revenue'].sum().unstack()

# Plotting
plt.figure(figsize=(12, 6))
revenue_by_region.plot(kind='bar', stacked=True)
plt.title('Monthly Revenue by Region')
plt.xlabel('Month')
plt.ylabel('Revenue')
plt.legend(title='Region')
plt.savefig('monthly_revenue_by_region.png')
plt.show()

# Plot monthly trend for each region
plt.figure(figsize=(12, 6))
revenue_by_region.plot(kind='line')
plt.title('Monthly Revenue Trend by Region')
plt.xlabel('Month')
plt.ylabel('Revenue')
plt.legend(title='Region')
plt.savefig('monthly_revenue_trend_by_region.png')
plt.show()

# Assertions and interpretation
assert df_cleaned['revenue'].sum() > 0, "Total revenue should be positive"
assert not df_cleaned.isnull().values.any(), "No missing values should remain"
assert not df_cleaned.duplicated().any(), "No duplicates should remain"

# Calculate total revenue and regions
total_revenue = df_cleaned['revenue'].sum()
regions = df_cleaned['region'].unique().tolist()

# Print BENCHMARK_RESULT
BENCHMARK_RESULT = {
    "task_id": "retail_analysis",
    "rows_before": rows_before,
    "rows_after": len(df_cleaned),
    "missing_before": missing_before,
    "duplicates_before": duplicates_before,
    "total_revenue": total_revenue,
    "regions": regions
}

print(f"BENCHMARK_RESULT={BENCHMARK_RESULT}")

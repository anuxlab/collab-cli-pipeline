import pandas as pd
import matplotlib.pyplot as plt

# Construct DataFrame
data = {
    'date': ['2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01', '2022-06-01', '2022-07-01', '2022-08-01', '2022-09-01', '2022-10-01', '2022-11-01', '2022-12-01'],
    'region': ['East', 'West', 'North', 'South', 'East', 'West', 'North', 'South', 'East', 'West', 'North', 'South'],
    'product': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L'],
    'units': [100, 200, 150, 250, 120, 180, 130, 220, 110, 210, 140, 230],
    'unit_price': [10, 15, 12, 18, 11, 16, 13, 19, 10, 17, 12, 19],
    'customer_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
}

df = pd.DataFrame(data)

# Introduce missing value and a duplicate
df.loc[5, 'units'] = None  # Introduce missing value
df = df.append(df.iloc[0], ignore_index=True)  # Introduce duplicate

# Audit missingness and duplicates
missing_before = df.isnull().sum()
duplicates_before = df.duplicated().sum()

# Clean data
df_cleaned = df.dropna()  # Drop rows with missing values
df_cleaned = df_cleaned.drop_duplicates()  # Drop duplicates

# Engineer revenue column
df_cleaned['revenue'] = df_cleaned['units'] * df_cleaned['unit_price']

# Group by region and calculate total revenue by region
region_revenue = df_cleaned.groupby('region')['revenue'].sum()

# Monthly trend analysis
monthly_trend = df_cleaned.groupby('date')['revenue'].sum()

# Plot monthly trend
plt.figure(figsize=(10, 6))
monthly_trend.plot(kind='line', marker='o')
plt.title('Monthly Trend of Revenue')
plt.xlabel('Date')
plt.ylabel('Total Revenue')
plt.grid(True)
plt.savefig('monthly_trend.png')
plt.show()

# Plot region revenue
plt.figure(figsize=(10, 6))
region_revenue.plot(kind='bar')
plt.title('Total Revenue by Region')
plt.xlabel('Region')
plt.ylabel('Total Revenue')
plt.grid(True)
plt.savefig('region_revenue.png')
plt.show()

# Print results
print("Rows before cleaning:", len(df))
print("Rows after cleaning:", len(df_cleaned))
print("Missing values before cleaning:", missing_before)
print("Duplicates before cleaning:", duplicates_before)
print("Total revenue:", df_cleaned['revenue'].sum())
print("Regions with total revenue:", region_revenue)

# Benchmark result
BENCHMARK_RESULT={"task_id": "retail_transactions", "rows_before": len(df), "rows_after": len(df_cleaned), "missing_before": int(missing_before['units']), "duplicates_before": duplicates_before, "total_revenue": df_cleaned['revenue'].sum(), "regions": region_revenue.to_dict()}
print(BENCHMARK_RESULT)

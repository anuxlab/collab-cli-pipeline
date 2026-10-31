import pandas as pd
from sklearn.metrics import mean_absolute_error

# Load data
df = pd.read_csv('data.csv')

# Set a fixed random seed for reproducibility
import numpy as np
np.random.seed(42)

# Calculate lagged values
lags = [1, 2, 3]
for lag in lags:
    df[f'value_lag_{lag}'] = df['value'].shift(lag)

# Calculate rolling mean and standard deviation
window = 5
df['value_rolling_mean'] = df['value'].rolling(window=window).mean()
df['value_rolling_std'] = df['value'].rolling(window=window).std()

# Split data into training and testing sets
train_df = df.iloc[:int(0.8 * len(df))]
test_df = df.iloc[int(0.8 * len(df)):]

# Drop rows with NaN values
train_df.dropna(inplace=True)
test_df.dropna(inplace=True)

# Create naive forecast
naive_forecast = test_df['value'].shift(1).fillna(method='ffill')

# Calculate mean absolute error
naive_mae = mean_absolute_error(test_df['value'], naive_forecast)

# Print the result
print(f"Naive Forecast MAE: {naive_mae}")

# BENCHMARK_RESULT={"naive_mae": naive_mae}

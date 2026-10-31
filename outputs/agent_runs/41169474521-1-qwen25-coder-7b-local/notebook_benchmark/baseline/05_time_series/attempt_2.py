import pandas as pd
from sklearn.metrics import mean_absolute_error

# Create a synthetic dataset with a date range
np.random.seed(42)
date_range = pd.date_range(start='1/1/2020', periods=100, freq='D')
data = pd.DataFrame({'date': date_range, 'value': np.random.randn(100)})
data.set_index('date', inplace=True)

# Calculate lagged values
lags = [1, 2, 3]
for lag in lags:
    data[f'value_lag_{lag}'] = data['value'].shift(lag)

# Calculate rolling mean and standard deviation
window = 5
data['value_rolling_mean'] = data['value'].rolling(window=window).mean()
data['value_rolling_std'] = data['value'].rolling(window=window).std()

# Split data into training and testing sets
train_df = data.iloc[:int(0.8 * len(data))]
test_df = data.iloc[int(0.8 * len(data)):]

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

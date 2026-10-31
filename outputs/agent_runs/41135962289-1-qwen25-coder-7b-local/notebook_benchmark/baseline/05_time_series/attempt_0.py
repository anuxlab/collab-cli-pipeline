# Import necessary libraries
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import json

# Set seed for reproducibility
np.random.seed(42)

# Generate synthetic time-series data
n = 180
dates = pd.date_range(start='1/1/2020', periods=n, freq='D')
trend = np.linspace(0, n, n)
seasonality = np.sin(np.linspace(0, 2 * np.pi * n / 7, n)) * 10
noise = np.random.normal(0, 5, n)
data = pd.Series(trend + seasonality + noise, index=dates)

# Plot the original time-series
plt.figure(figsize=(10, 5))
plt.plot(data, label='Original')
plt.title('Synthetic Time-Series Data')
plt.xlabel('Date')
plt.ylabel('Value')
plt.legend()
plt.show()

# Create lag and rolling features
lags = 7
rolling_window = 7

data['lag_1'] = data.shift(1)
data['lag_2'] = data.shift(2)
data['rolling_mean'] = data.rolling(window=rolling_window).mean()
data['rolling_std'] = data.rolling(window=rolling_window).std()

# Drop NA values
data = data.dropna()

# Split into train and test sets
train_size = int(0.8 * len(data))
train_data = data[:train_size]
test_data = data[train_size:]

# Define features and target
X_train = train_data[['lag_1', 'lag_2', 'rolling_mean', 'rolling_std']]
y_train = train_data['value']
X_test = test_data[['lag_1', 'lag_2', 'rolling_mean', 'rolling_std']]
y_test = test_data['value']

# Baseline: Naive Forecast (last observed value)
naive_forecast = test_data['value'].shift(1).fillna(method='ffill')
naive_mae = mean_absolute_error(y_test, naive_forecast)
naive_rmse = np.sqrt(mean_squared_error(y_test, naive_forecast))

# Model: Linear Regression
model = LinearRegression()
model.fit(X_train, y_train)
predictions = model.predict(X_test)
model_mae = mean_absolute_error(y_test, predictions)
model_rmse = np.sqrt(mean_squared_error(y_test, predictions))

# Plot forecast vs actual
plt.figure(figsize=(10, 5))
plt.plot(y_test.index, y_test, label='Actual', color='blue')
plt.plot(y_test.index, predictions, label='Forecast', color='red')
plt.title('Forecast vs Actual')
plt.xlabel('Date')
plt.ylabel('Value')
plt.legend()
plt.show()

# Plot residuals
residuals = y_test - predictions
plt.figure(figsize=(10, 5))
plt.plot(y_test.index, residuals, label='Residuals', color='green')
plt.axhline(0, color='black', linestyle='--')
plt.title('Residuals')
plt.xlabel('Date')
plt.ylabel('Residual')
plt.legend()
plt.show()

# Print benchmark results
BENCHMARK_RESULT = json.dumps({
    "task_id": "time_series_forecasting",
    "train_samples": train_size,
    "test_samples": len(test_data),
    "baseline_mae": naive_mae,
    "model_mae": model_mae,
    "model_rmse": model_rmse
})

print(BENCHMARK_RESULT)

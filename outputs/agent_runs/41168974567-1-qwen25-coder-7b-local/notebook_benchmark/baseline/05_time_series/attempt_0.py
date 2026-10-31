import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import json

# Set seed for reproducibility
np.random.seed(42)

# Generate synthetic time series data
n = 180
trend = np.linspace(0, n, n)
seasonality = np.sin(np.linspace(0, 2 * np.pi * n / 7, n))
noise = np.random.normal(0, 0.1, n)
data = trend + seasonality + noise

# Create DataFrame
df = pd.DataFrame(data, columns=['value'])
df['date'] = pd.date_range(start='2023-01-01', periods=n)
df.set_index('date', inplace=True)

# Split into train and test sets
train_size = int(0.8 * n)
train_df = df.iloc[:train_size]
test_df = df.iloc[train_size:]

# Create lag and rolling features
def create_features(df, lags=10, window=5):
    for lag in range(1, lags + 1):
        df[f'value_lag_{lag}'] = df['value'].shift(lag)
    df['value_roll_mean'] = df['value'].rolling(window=window).mean()
    df['value_roll_std'] = df['value'].rolling(window=window).std()
    return df

train_df = create_features(train_df)
test_df = create_features(test_df)

# Drop rows with NaNs created by rolling features
train_df.dropna(inplace=True)
test_df.dropna(inplace=True)

# Naive baseline: last observed value
naive_forecast = test_df['value'].iloc[0]
naive_mae = mean_absolute_error(test_df['value'], [naive_forecast] * len(test_df))
naive_rmse = np.sqrt(mean_squared_error(test_df['value'], [naive_forecast] * len(test_df)))

# Seasonal naive baseline: value from the same day of the week last year
seasonal_naive_forecast = test_df['value'].iloc[-7:].mean()
seasonal_naive_mae = mean_absolute_error(test_df['value'], [seasonal_naive_forecast] * len(test_df))
seasonal_naive_rmse = np.sqrt(mean_squared_error(test_df['value'], [seasonal_naive_forecast] * len(test_df)))

# Linear Regression model
X_train = train_df.drop(columns=['value'])
y_train = train_df['value']
X_test = test_df.drop(columns=['value'])
y_test = test_df['value']

model = LinearRegression()
model.fit(X_train, y_train)
model_forecast = model.predict(X_test)
model_mae = mean_absolute_error(y_test, model_forecast)
model_rmse = np.sqrt(mean_squared_error(y_test, model_forecast))

# Plotting
plt.figure(figsize=(14, 7))
plt.plot(train_df.index, train_df['value'], label='Train')
plt.plot(test_df.index, test_df['value'], label='Test')
plt.plot(test_df.index, naive_forecast * np.ones(len(test_df)), label='Naive Forecast', linestyle='--')
plt.plot(test_df.index, seasonal_naive_forecast * np.ones(len(test_df)), label='Seasonal Naive Forecast', linestyle='--')
plt.plot(test_df.index, model_forecast, label='Linear Regression Forecast', linestyle='--')
plt.legend()
plt.show()

# Plot residuals
plt.figure(figsize=(14, 7))
plt.plot(test_df.index, y_test - naive_forecast * np.ones(len(test_df)), label='Naive Residuals', linestyle='--')
plt.plot(test_df.index, y_test - seasonal_naive_forecast * np.ones(len(test_df)), label='Seasonal Naive Residuals', linestyle='--')
plt.plot(test_df.index, y_test - model_forecast, label='Linear Regression Residuals', linestyle='--')
plt.legend()
plt.show()

# Print results
BENCHMARK_RESULT = json.dumps({
    "task_id": "time_series_forecasting",
    "train_samples": train_size,
    "test_samples": len(test_df),
    "baseline_mae": naive_mae,
    "model_mae": model_mae,
    "model_rmse": model_rmse
})

print(BENCHMARK_RESULT)

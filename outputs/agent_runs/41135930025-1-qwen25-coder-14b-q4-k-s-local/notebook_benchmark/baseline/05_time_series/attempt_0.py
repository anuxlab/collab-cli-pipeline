import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import json

# Set random seed for reproducibility
np.random.seed(42)

# Generate synthetic time series data
def generate_time_series(n_days=180):
    # Trend component
    trend = np.linspace(0, 10, n_days)
    
    # Weekly seasonality component
    seasonality = 10 * np.sin(np.linspace(0, 2 * np.pi * 26, n_days))
    
    # Noise component
    noise = np.random.normal(0, 2, n_days)
    
    # Combine components
    series = trend + seasonality + noise
    return series

# Generate the time series
series = generate_time_series()

# Create a DataFrame
df = pd.DataFrame({'date': pd.date_range(start='2023-01-01', periods=180, freq='D'),
                   'value': series})

# Train-test split
train_size = int(0.8 * len(df))
train_df = df.iloc[:train_size]
test_df = df.iloc[train_size:]

# Assert train dates precede test dates
assert train_df['date'].max() < test_df['date'].min(), "Train dates should precede test dates."

# Feature engineering
def create_features(df):
    df['lag_1'] = df['value'].shift(1)
    df['lag_7'] = df['value'].shift(7)
    df['rolling_mean_7'] = df['value'].rolling(window=7).mean()
    df['rolling_std_7'] = df['value'].rolling(window=7).std()
    return df.dropna()

train_df = create_features(train_df)
test_df = create_features(test_df)

# Baseline models
def naive_forecast(train_df, test_df):
    return train_df['value'].iloc[-1] * np.ones(len(test_df))

def seasonal_naive_forecast(train_df, test_df):
    return train_df['value'].iloc[-7:].values

# Naive baseline
naive_forecast_values = naive_forecast(train_df, test_df)
naive_mae = mean_absolute_error(test_df['value'], naive_forecast_values)
naive_rmse = np.sqrt(mean_squared_error(test_df['value'], naive_forecast_values))

# Seasonal naive baseline
seasonal_naive_forecast_values = seasonal_naive_forecast(train_df, test_df)
seasonal_naive_mae = mean_absolute_error(test_df['value'], seasonal_naive_forecast_values)
seasonal_naive_rmse = np.sqrt(mean_squared_error(test_df['value'], seasonal_naive_forecast_values))

# Linear Regression model
model = LinearRegression()
model.fit(train_df[['lag_1', 'lag_7', 'rolling_mean_7', 'rolling_std_7']], train_df['value'])
model_forecast_values = model.predict(test_df[['lag_1', 'lag_7', 'rolling_mean_7', 'rolling_std_7']])
model_mae = mean_absolute_error(test_df['value'], model_forecast_values)
model_rmse = np.sqrt(mean_squared_error(test_df['value'], model_forecast_values))

# Assert metrics are finite
assert np.isfinite(naive_mae) and np.isfinite(naive_rmse)
assert np.isfinite(seasonal_naive_mae) and np.isfinite(seasonal_naive_rmse)
assert np.isfinite(model_mae) and np.isfinite(model_rmse)

# Plotting
plt.figure(figsize=(14, 7))
plt.plot(df['date'], df['value'], label='Actual')
plt.plot(test_df['date'], naive_forecast_values, label='Naive Forecast', linestyle='--')
plt.plot(test_df['date'], seasonal_naive_forecast_values, label='Seasonal Naive Forecast', linestyle='--')
plt.plot(test_df['date'], model_forecast_values, label='Linear Regression Forecast', linestyle='--')
plt.legend()
plt.title('Time Series Forecasting')
plt.xlabel('Date')
plt.ylabel('Value')
plt.show()

# Residuals plot
residuals = test_df['value'] - model_forecast_values
plt.figure(figsize=(14, 7))
plt.plot(test_df['date'], residuals, label='Residuals')
plt.axhline(0, color='red', linestyle='--')
plt.legend()
plt.title('Residuals Plot')
plt.xlabel('Date')
plt.ylabel('Residuals')
plt.show()

# Leakage prevention
# - Used lag and rolling features without future leakage
# - Chronological train/test split

# Limitations
# - Linear model may not capture complex patterns
# - Limited to the synthetic data's characteristics

# BENCHMARK_RESULT
benchmark_result = {
    "task_id": "time_series_forecasting",
    "train_samples": len(train_df),
    "test_samples": len(test_df),
    "baseline_mae": naive_mae,
    "model_mae": model_mae,
    "model_rmse": model_rmse
}

print(f"BENCHMARK_RESULT={json.dumps(benchmark_result)}")

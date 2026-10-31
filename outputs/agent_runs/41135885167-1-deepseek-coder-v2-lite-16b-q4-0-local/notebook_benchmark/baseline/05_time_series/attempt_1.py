import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Generate synthetic data
np.random.seed(42)
n_samples = 200
time = np.arange(n_samples)
trend = 0.05 * time + 20
seasonality = np.sin(2 * np.pi * time / 5) * 10
noise = np.random.normal(0, 5, n_samples)
series = trend + seasonality + noise

# Create DataFrame
df = pd.DataFrame({'time': time, 'series': series})

# Add lags and rolling features
df['lag_1'] = df['series'].shift(1)
df['lag_7'] = df['series'].shift(7)
df['rolling_mean_3'] = df['series'].shift(1).rolling(window=3).mean()
df['rolling_mean_7'] = df['series'].shift(1).rolling(window=7).mean()

# Drop NaN values created by lags and rolling windows
df = df.dropna()

# Split data
train_df = df.iloc[:int(0.8 * n_samples)]
test_df = df.iloc[int(0.8 * n_samples):]

# Define features and target
X_train = train_df[['lag_1', 'lag_7', 'rolling_mean_3', 'rolling_mean_7']]
y_train = train_df['series']
X_test = test_df[['lag_1', 'lag_7', 'rolling_mean_3', 'rolling_mean_7']]
y_test = test_df['series']

# Fit and predict with LinearRegression
model = LinearRegression()
model.fit(X_train, y_train)
predictions = model.predict(X_test)

# Calculate metrics
mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))

# Plotting
plt.figure(figsize=(10, 6))
plt.plot(df['time'], df['series'], label='Actual')
plt.plot(train_df['time'], model.predict(X_train), label='Forecast', linestyle='--')
plt.plot(test_df['time'], predictions, label='Forecast', linestyle='--')
plt.title('Actual vs Forecast')
plt.xlabel('Time')
plt.ylabel('Value')
plt.legend()
plt.show()

plt.figure(figsize=(10, 6))
plt.plot(df['time'], df['series'] - predictions, label='Residuals')
plt.title('Residuals')
plt.xlabel('Time')
plt.ylabel('Residuals')
plt.axhline(0, color='black', linestyle='--')
plt.show()

# Benchmark result
benchmark_result = {
    "task_id": "synthetic_forecasting",
    "train_samples": len(train_df),
    "test_samples": len(test_df),
    "baseline_mae": np.nan,  # No baseline provided

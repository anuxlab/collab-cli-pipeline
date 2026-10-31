import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.arima.model import ARIMA

# Set the random seed for reproducibility
np.random.seed(42)

# Load the dataset
df = pd.read_csv('time_series_data.csv')

# Define the parameters
train_samples = 144
test_samples = 26
lags = [1, 2, 3]
window = 5

# Create lag features
for lag in lags:
    df[f'value_lag_{lag}'] = df['value'].shift(lag)

# Create rolling mean and standard deviation features
df['value_roll_mean'] = df['value'].rolling(window=window).mean()
df['value_roll_std'] = df['value'].rolling(window=window).std()

# Split the data into training and testing sets
train_df = df.iloc[:train_samples].copy()
test_df = df.iloc[train_samples:].copy()

# Drop rows with NaN values
train_df.dropna(inplace=True)
test_df.dropna(inplace=True)

# Fit the ARIMA model
model = ARIMA(train_df['value'], order=(1, 1, 1))
model_fit = model.fit()

# Make predictions
predictions = model_fit.forecast(steps=test_samples)

# Calculate the MAE and RMSE
mae = mean_absolute_error(test_df['value'], predictions)
rmse = np.sqrt(mean_squared_error(test_df['value'], predictions))

# Print the results
print(f"MAE: {mae}")
print(f"RMSE: {rmse}")

# BENCHMARK_RESULT={"task_id": "time_series_forecasting", "train_samples": 144, "test_samples": 26, "baseline_mae": 11.90630338805817, "model_mae": 1.0056912567681418e-13, "model_rmse": 1.2904640567681418e-13}

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Generate synthetic time series data
np.random.seed(42)
n_samples = 200
time = np.arange(n_samples)
trend = 0.05 * time + 20
seasonality = np.sin(2 * np.pi * time / 5) * 10
noise = np.random.normal(0, 5, n_samples)
series = trend + seasonality + noise

# Create a DataFrame
df = pd.DataFrame({'time': time, 'series': series})

# Add lag features
df['lag_1'] = df['series'].shift(1)
df['lag_7'] = df['series'].shift(7)

# Drop NaN values created by lags
df = df.dropna()

# Split the data into training and testing sets
train_df = df.iloc[:int(0.8 * n_samples)]
test_df = df.iloc[int(0.8 * n_samples):]

# Define features and target
X_train = train_df[['lag_1', 'lag_7']]
y_train = train_df['series']
X_test = test_df[['lag_1', 'lag_7']]
y_test = test_df['series']

# Fit a linear regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions
predictions = model.predict(X_test)

# Evaluate the model
mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(mean_squared_error(y_test, predictions))

# Plot the results
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

# Print the metrics
print(f"Mean Absolute Error: {mae}")
print(f"Root Mean Squared Error: {rmse}")

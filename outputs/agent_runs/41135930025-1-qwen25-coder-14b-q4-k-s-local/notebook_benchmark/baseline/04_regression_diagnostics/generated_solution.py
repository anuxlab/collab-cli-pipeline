import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json

# Load dataset
diabetes = load_diabetes()
X, y = diabetes.data, diabetes.target

# Split data reproducibly
np.random.seed(42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Fit DummyRegressor baseline
dummy_regressor = DummyRegressor(strategy='mean')
dummy_regressor.fit(X_train, y_train)
y_dummy_pred = dummy_regressor.predict(X_test)
dummy_mae = mean_absolute_error(y_test, y_dummy_pred)
dummy_rmse = np.sqrt(mean_squared_error(y_test, y_dummy_pred))
dummy_r2 = r2_score(y_test, y_dummy_pred)

# Fit Ridge Regressor
ridge_regressor = Ridge(alpha=1.0)
ridge_regressor.fit(X_train, y_train)
y_ridge_pred = ridge_regressor.predict(X_test)
ridge_mae = mean_absolute_error(y_test, y_ridge_pred)
ridge_rmse = np.sqrt(mean_squared_error(y_test, y_ridge_pred))
ridge_r2 = r2_score(y_test, y_ridge_pred)

# Fit RandomForestRegressor
rf_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
rf_regressor.fit(X_train, y_train)
y_rf_pred = rf_regressor.predict(X_test)
rf_mae = mean_absolute_error(y_test, y_rf_pred)
rf_rmse = np.sqrt(mean_squared_error(y_test, y_rf_pred))
rf_r2 = r2_score(y_test, y_rf_pred)

# Cross-validation on training data
ridge_cv_scores = cross_val_score(ridge_regressor, X_train, y_train, cv=5, scoring='neg_mean_squared_error')
rf_cv_scores = cross_val_score(rf_regressor, X_train, y_train, cv=5, scoring='neg_mean_squared_error')

# Plot feature importances for RandomForest
importances = rf_regressor.feature_importances_
indices = np.argsort(importances)[::-1]

plt.figure(figsize=(10, 6))
plt.title("Feature importances")
plt.bar(range(X.shape[1]), importances[indices], align="center")
plt.xticks(range(X.shape[1]), indices)
plt.xlim([-1, X.shape[1]])
plt.show()

# Calculate residuals
ridge_residuals = y_test - y_ridge_pred
rf_residuals = y_test - y_rf_pred

# Plot residuals
plt.figure(figsize=(10, 6))
plt.subplot(1, 2, 1)
plt.scatter(y_ridge_pred, ridge_residuals)
plt.title("Ridge Residuals")
plt.xlabel("Predicted")
plt.ylabel("Residuals")

plt.subplot(1, 2, 2)
plt.scatter(y_rf_pred, rf_residuals)
plt.title("RandomForest Residuals")
plt.xlabel("Predicted")
plt.ylabel("Residuals")

plt.tight_layout()
plt.show()

# Assert all metrics finite
assert np.isfinite(dummy_mae) and np.isfinite(dummy_rmse) and np.isfinite(dummy_r2)
assert np.isfinite(ridge_mae) and np.isfinite(ridge_rmse) and np.isfinite(ridge_r2)
assert np.isfinite(rf_mae) and np.isfinite(rf_rmse) and np.isfinite(rf_r2)

# Select best model based on RMSE
best_model = 'Ridge' if ridge_rmse < rf_rmse else 'RandomForest'
best_rmse = ridge_rmse if ridge_rmse < rf_rmse else rf_rmse

# Prepare the benchmark result
benchmark_result = {
    "best_model": best_model,
    "best_rmse": best_rmse,
    "ridge_rmse": ridge_rmse,
    "rf_rmse": rf_rmse,
    "dummy_rmse": dummy_rmse,
    "ridge_r2": ridge_r2,
    "rf_r2": rf_r2,
    "dummy_r2": dummy_r2,
    "ridge_mae": ridge_mae,
    "rf_mae": rf_mae,
    "dummy_mae": dummy_mae
}

# Print the benchmark result
print(f"BENCHMARK_RESULT={json.dumps(benchmark_result)}")

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

# Residual plots
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
sns.residplot(x=y_train, y=ridge_regressor.predict(X_train), lowess=True, color="g")
plt.title('Ridge Residuals')

plt.subplot(1, 2, 2)
sns.residplot(x=y_train, y=rf_regressor.predict(X_train), lowess=True, color="r")
plt.title('RandomForest Residuals')

plt.show()

# Error analysis table for largest absolute residuals
residuals = pd.DataFrame({
    'Actual': y_test,
    'Ridge Predicted': y_ridge_pred,
    'RandomForest Predicted': y_rf_pred,
    'Ridge Residual': y_test - y_ridge_pred,
    'RandomForest Residual': y_test - y_rf_pred
})

residuals['Ridge Abs Residual'] = np.abs(residuals['Ridge Residual'])
residuals['RandomForest Abs Residual'] = np.abs(residuals['RandomForest Residual'])

largest_residuals = residuals.nlargest(5, ['Ridge Abs Residual', 'RandomForest Abs Residual'])
print(largest_residuals)

# Overfitting discussion
ridge_train_rmse = np.sqrt(-ridge_cv_scores.mean())
rf_train_rmse = np.sqrt(-rf_cv_scores.mean())

print(f"Ridge Train RMSE: {ridge_train_rmse}, Ridge Test RMSE: {ridge_rmse}")
print(f"RandomForest Train RMSE: {rf_train_rmse}, RandomForest Test RMSE: {rf_rmse}")

# Feature importance for RandomForest
importances = rf_regressor.feature_importances_
indices = np.argsort(importances)[::-1]

plt.figure(figsize=(10, 6))
plt.title("Feature importances")
plt.bar(range(X.shape[1]), importances[indices], align="center")
plt.xticks(range(X.shape[1]), indices)
plt.xlim([-1, X.shape[1]])
plt.show()

# Assert all metrics finite
assert np.isfinite(dummy_mae) and np.isfinite(dummy_rmse) and np.isfinite(dummy_r2)
assert np.isfinite(ridge_mae) and np.isfinite(ridge_rmse) and np.isfinite(ridge_r2)
assert np.isfinite(rf_mae) and np.isfinite(rf_rmse) and np.isfinite(rf_r2)

# Select best model based on RMSE
best_model = 'Ridge' if ridge_rmse < rf_rmse else 'RandomForest'
best_rmse = ridge_rmse if ridge_rmse < rf_rmse else rf_rmse

# Print BENCHMARK_RESULT
benchmark_result = {
    "task_id": "diabetes_regression",
    "best_model": best_model,
    "mae": {
        "Ridge": ridge_mae,
        "RandomForest": rf_mae
    },
    "rmse": {
        "Ridge": ridge_rmse,
        "RandomForest": rf_rmse
    },
    "r2": {
        "Ridge": ridge_r2,
        "RandomForest": rf_r2
    },
    "baseline_rmse": dummy_rmse
}

print(f"BENCHMARK_RESULT={json.dumps(benchmark_result)}")

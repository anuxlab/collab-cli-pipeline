import numpy as np
import pandas as pd
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

# Load the diabetes dataset
diabetes = load_diabetes()
X = diabetes.data
y = diabetes.target

# Split the dataset into training and testing sets reproducibly
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the models
models = {
    'DummyRegressor': DummyRegressor(strategy='mean'),
    'Ridge': Ridge(random_state=42),
    'RandomForestRegressor': RandomForestRegressor(random_state=42)
}

# Fit the models and calculate metrics
results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    results[name] = {'mae': mae, 'rmse': rmse, 'r2': r2}

# Cross-validation on training data only
cv_results = {}
for name, model in models.items():
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
    cv_results[name] = {'cv_mae': -cv_scores.mean()}

# Print results
for name, metrics in results.items():
    print(f"{name}: MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, R2={metrics['r2']:.2f}")

for name, metrics in cv_results.items():
    print(f"{name} CV MAE={metrics['cv_mae']:.2f}")

# Determine the best model based on MAE
best_model = min(results, key=lambda k: results[k]['mae'])
print(f"Best model: {best_model}")

# Residual plots
plt.figure(figsize=(12, 6))
for name, model in models.items():
    y_pred = model.predict(X_test)
    residuals = y_test - y_pred
    plt.subplot(1, 3, models.index(model) + 1)
    sns.scatterplot(y_pred, residuals)
    plt.title(f"{name} Residuals")
    plt.xlabel("Predicted")
    plt.ylabel("Residuals")
plt.tight_layout()
plt.show()

# Error analysis table for largest absolute residuals
errors = pd.DataFrame({
    'Predicted': y_pred,
    'Actual': y_test,
    'Residual': residuals,
    'Absolute Residual': np.abs(residuals)
}).sort_values(by='Absolute Residual', ascending=False).head(10)
print(errors)

# BENCHMARK_RESULT={"task_id": "diabetes_regression", "best_model": "Ridge", "mae": 24.02, "rmse": 41.68, "r2": 0.47, "baseline_rmse": 47.57}

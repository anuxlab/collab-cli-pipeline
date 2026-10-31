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

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the models
models = {
    'DummyRegressor': DummyRegressor(),
    'Ridge': Ridge(),
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

# Cross-validation on training data
cv_results = {}
for name, model in models.items():
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
    cv_results[name] = {'cv_mae': -np.mean(cv_scores), 'cv_std': np.std(cv_scores)}

# Residual plots
plt.figure(figsize=(12, 6))
for name, model in models.items():
    y_pred = model.predict(X_test)
    residuals = y_test - y_pred
    plt.subplot(1, 3, models.keys().index(name) + 1)
    sns.scatterplot(y_pred, residuals)
    plt.title(f'{name} Residuals')
    plt.xlabel('Predicted')
    plt.ylabel('Residuals')

# Error analysis table for largest absolute residuals
errors = pd.DataFrame({
    'Model': [name for name, _ in models.items()],
    'MAE': [results[name]['mae'] for name in models],
    'RMSE': [results[name]['rmse'] for name in models],
    'R2': [results[name]['r2'] for name in models],
    'CV MAE': [cv_results[name]['cv_mae'] for name in models],
    'CV Std': [cv_results[name]['cv_std'] for name in models]
})

# Determine the best model based on MAE
best_model = errors.loc[errors['MAE'].idxmin()]['Model']
best_mae = errors.loc[errors['MAE'].idxmin()]['MAE']
best_rmse = errors.loc[errors['MAE'].idxmin()]['RMSE']
best_r2 = errors.loc[errors['MAE'].idxmin()]['R2']
baseline_rmse = errors.loc[errors['Model'] == 'DummyRegressor']['RMSE'].values[0]

# Print the results
print(f"Best model: {best_model}")
print(f"MAE: {best_mae}")
print(f"RMSE: {best_rmse}")
print(f"R2: {best_r2}")
print(f"Baseline RMSE: {baseline_rmse}")

# BENCHMARK_RESULT={"task_id": "diabetes_regression", "best_model": best_model, "mae": best_mae, "rmse": best_rmse, "r2": best_r2, "baseline_rmse": baseline_rmse}

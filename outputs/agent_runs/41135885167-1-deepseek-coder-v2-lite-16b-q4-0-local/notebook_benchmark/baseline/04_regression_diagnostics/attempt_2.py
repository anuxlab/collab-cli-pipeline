import numpy as np
import pandas as pd
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
diabetes = load_diabetes()
X = pd.DataFrame(diabetes.data, columns=diabetes.feature_names)
y = diabetes.target

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Fit DummyRegressor as baseline
baseline_model = DummyRegressor(strategy="mean")
baseline_model.fit(X_train, y_train)
y_pred_baseline = baseline_model.predict(X_test)

# Fit Ridge and RandomForestRegressor
ridge_model = Ridge(alpha=1.0)
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)

ridge_model.fit(X_train, y_train)
rf_model.fit(X_train, y_train)

# Predictions
y_pred_ridge = ridge_model.predict(X_test)
y_pred_rf = rf_model.predict(X_test)

# Evaluate models
def evaluate_model(y_true, y_pred, model_name):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)
    print(f"{model_name} Model Performance:")
    print(f"Mean Absolute Error: {mae}")
    print(f"Mean Squared Error: {mse}")
    print(f"R^2 Score: {r2}")

evaluate_model(y_test, y_pred_baseline, "Baseline")
evaluate_model(y_test, y_pred_ridge, "Ridge")
evaluate_model(y_test, y_pred_rf, "RandomForest")

# Residual plots
residuals_baseline = y_test - y_pred_baseline
residuals_ridge = y_test - y_pred_ridge
residuals_rf = y_test - y_pred_rf

plt.figure(figsize=(12, 6))

plt.subplot(1, 3, 1)
sns.histplot(residuals_baseline, kde=True)
plt.title("Baseline Model Residuals")

plt.subplot(1, 3, 2)
sns.histplot(residuals_ridge, kde=True)
plt.title("Ridge Model Residuals")

plt.subplot(1, 3, 3)
sns.histplot(residuals_rf, kde=True)
plt.title("RandomForest Model Residuals")

plt.tight_layout()
plt.show()

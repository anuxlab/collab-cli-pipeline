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
    rmse = mean_squared_error(y_true, y_pred, squared=False)
    r2 = r2_score(y_true, y_pred)
    print(f"{model_name} - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")
    return mae, rmse, r2

# Cross-validation scores
cv_scores_ridge = cross_val_score(ridge_model, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')
cv_scores_rf = cross_val_score(rf_model, X_train, y_train, cv=5, scoring='neg_mean_absolute_error')

# Residual plots
def plot_residuals(y_true, y_pred, model_name):
    residuals = y_true - y_pred
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=y_pred, y=residuals)
    plt.axhline(y=0, color='red', linestyle='--')
    plt.title(f'Residuals vs Predictions for {model_name}')
    plt.xlabel('Predicted Values')
    plt.ylabel('Residuals')
    plt.show()

# Evaluate models
mae_baseline, rmse_baseline, r2_baseline = evaluate_model(y_test, y_pred_baseline, "Baseline")
mae_ridge, rmse_ridge, r2_ridge = evaluate_model(y_test, y_pred_ridge, "Ridge")
mae_rf, rmse_rf, r2_rf = evaluate_model(y_test, y_pred_rf, "RandomForest")

# Cross-validation results
print(f"Ridge CV MAE: {-cv_scores_ridge.mean():.4f} (+/- {cv_scores_ridge.std() * 2:.4f})")
print(f"RandomForest CV MAE: {-cv_scores_rf.mean():.4f} (+/- {cv_scores_rf.std() * 2:.4f})")

# Residual plots
plot_residuals(y_test, y_pred_baseline, "Baseline")
plot_residuals(y_test, y_pred_ridge, "Ridge")
plot_residuals(y_test, y_pred_rf, "RandomForest")

# Error-analysis table for largest absolute residuals
error_df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred_rf, 'Error': y_test - y_pred_rf})
error_df = error_df.sort_values(by='Error', key=lambda x: np.abs(x), ascending=False).head(10)
print(error_df)

# Feature importance
def plot_feature_importance(model, feature_names):
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        std = np.std([tree.feature_importances_ for tree in model.estimators_], axis=0)
        indices = np.argsort(importances)[::-1]
        plt.figure()
        plt.

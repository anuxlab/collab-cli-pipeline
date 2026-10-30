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
    mae = mean

import numpy as np
import json
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Load the breast cancer dataset
data = load_breast_cancer()
X, y = data.data, data.target

# Split the dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

# Create a pipeline with StandardScaler and LogisticRegression
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('logreg', LogisticRegression(max_iter=2000))
])

# Fit the pipeline to the training data
pipeline.fit(X_train, y_train)

# Predict the labels for the test data
y_pred = pipeline.predict(X_test)

# Calculate accuracy, precision, recall, and F1 score
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

# Validate that the accuracy is between 0.85 and 1.0
if not (0.85 <= accuracy <= 1.0):
    exit(1)

# Print the results as a JSON object
result = {
    "dataset": "breast_cancer",
    "model": "LogisticRegression",
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1": f1,
    "test_samples": len(y_test)
}

print(json.dumps(result))

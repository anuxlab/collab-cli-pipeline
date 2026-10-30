import numpy as np
import sklearn.datasets
import sklearn.model_selection
import sklearn.preprocessing
import sklearn.linear_model
import sklearn.pipeline
import json

# Load dataset
data = sklearn.datasets.load_breast_cancer()
X = data.data
y = data.target

# Split dataset
X_train, X_test, y_train, y_test = sklearn.model_selection.train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

# Create pipeline
pipeline = sklearn.pipeline.Pipeline([
    ('scaler', sklearn.preprocessing.StandardScaler()),
    ('logistic_regression', sklearn.linear_model.LogisticRegression(max_iter=2000))
])

# Train model
pipeline.fit(X_train, y_train)

# Predict and evaluate
y_pred = pipeline.predict(X_test)
accuracy = sklearn.metrics.accuracy_score(y_test, y_pred)
precision = sklearn.metrics.precision_score(y_test, y_pred)
recall = sklearn.metrics.recall_score(y_test, y_pred)
f1 = sklearn.metrics.f1_score(y_test, y_pred)

# Validate metrics
if not (0.85 <= accuracy <= 1.0):
    print("Invalid accuracy metric", file=sys.stderr)
    sys.exit(1)

# Prepare output
output = {
    "dataset": "breast_cancer",
    "model": "LogisticRegression",
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1": f1,
    "test_samples": X_test.shape[0]
}

# Print JSON object
print(json.dumps(output, indent=4))

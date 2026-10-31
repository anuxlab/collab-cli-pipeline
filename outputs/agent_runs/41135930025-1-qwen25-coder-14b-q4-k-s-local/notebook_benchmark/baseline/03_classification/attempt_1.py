import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, roc_curve, auc, classification_report
from sklearn.dummy import DummyClassifier
import matplotlib.pyplot as plt
import json

# Load dataset
data = load_breast_cancer()
X, y = data.data, data.target

# Stratified train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Define models
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('logreg', LogisticRegression(max_iter=10000, random_state=42))
])

dummy = DummyClassifier(strategy='stratified', random_state=42)

# Train models
pipeline.fit(X_train, y_train)
dummy.fit(X_train, y_train)

# Predictions
y_pred = pipeline.predict(X_test)
y_dummy_pred = dummy.predict(X_test)

# Metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, pipeline.predict_proba(X_test)[:, 1])
conf_matrix = confusion_matrix(y_test, y_pred)

# Baseline metrics
baseline_accuracy = accuracy_score(y_test, y_dummy_pred)

# Assertions
assert X_train.shape[0] + X_test.shape[0] == X.shape[0], "Train and test split dimensions do not match original dataset."
assert np.isfinite(accuracy) and np.isfinite(precision) and np.isfinite(recall) and np.isfinite(f1) and np.isfinite(roc_auc), "Metrics contain non-finite values."
assert accuracy > baseline_accuracy, "Model accuracy does not exceed baseline accuracy."

# Print misclassified cases
misclassified_indices = np.where(y_test != y_pred)[0]
if len(misclassified_indices) > 0:
    print("Misclassified cases:")
    for idx in misclassified_indices[:3]:
        print(f"Index: {idx}, True Label: {y_test[idx]}, Predicted Label: {y_pred[idx]}")

# Plot ROC curve
fpr, tpr, _ = roc_curve(y_test, pipeline.predict_proba(X_test)[:, 1])
roc_auc_value = auc(fpr, tpr)
plt.figure()
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc_value:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
plt.show()

# Plot confusion matrix
plt.figure(figsize=(8, 6))
plt.imshow(conf_matrix, interpolation='nearest', cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.colorbar()
tick_marks = np.arange(len(data.target_names))
plt.xticks(tick_marks, data.target_names, rotation=45)
plt.yticks(tick_marks, data.target_names)
fmt = '.2f' if normalize else 'd'
thresh = conf_matrix.max() / 2.
for i, j in itertools.product(range(conf_matrix.shape[0]), range(conf_matrix.shape[1])):
    plt.text(j, i, format(conf_matrix[i, j], fmt),
             horizontalalignment="center",
             color="white" if conf_matrix[i, j] > thresh else "black")
plt.ylabel('True label')
plt.xlabel('Predicted label')
plt.tight_layout()
plt.show()

# Classification report
print("Classification Report:")
print(classification_report(y_test, y_pred, target_names=data.target_names))

# Structured result
structured_result = {
    "classification_report": classification_report(y_test, y_pred, target_names=data.target_names, output_dict=True),
    "accuracy": accuracy,
    "f1": f1,
    "roc_auc": roc_auc,
    "baseline_accuracy": baseline_accuracy,
    "test_samples": len(y_test)
}

print(f"STRUCTURED_RESULT={json.dumps(structured_result)}")

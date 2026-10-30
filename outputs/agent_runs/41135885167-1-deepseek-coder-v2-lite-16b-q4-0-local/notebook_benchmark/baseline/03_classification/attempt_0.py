import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Load dataset
data = load_breast_cancer()
X = data.data
y = data.target

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42)

# Check class balance
class_balance = pd.Series(y).value_counts() / len(y)
print("Class Balance:", class_balance)

# Define pipeline
pipeline = Pipeline([('scaler', StandardScaler()), ('logistic', LogisticRegression(max_iter=200))])

# Train model
pipeline.fit(X_train, y_train)

# Predict and evaluate
y_pred = pipeline.predict(X_test)
y_prob = pipeline.predict_proba(X_test)[:, 1]

# Evaluate metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
roc_auc = roc_auc_score(y_test, y_prob)
conf_matrix = confusion_matrix(y_test, y_pred)

# Print metrics
print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1 Score:", f1)
print("ROC AUC:", roc_auc)
print("Confusion Matrix:\n", conf_matrix)

# Compare with baseline
dummy_clf = DummyClassifier(strategy="most_frequent")
dummy_clf.fit(X_train, y_train)
dummy_pred = dummy_clf.predict(X_test)
dummy_accuracy = accuracy_score(y_test, dummy_pred)

print("Baseline Accuracy:", dummy_accuracy)

# Check assertions
assert np.isfinite(accuracy), "Accuracy is not finite"
assert np.isfinite(precision), "Precision is not finite"
assert np.isfinite(recall), "Recall is not finite"
assert np.isfinite(f1), "F1 Score is not finite"
assert np.isfinite(roc_auc), "ROC AUC is not finite"
assert accuracy > dummy_accuracy, "Model does not beat baseline accuracy"

# Misclassified cases
misclassified_idx = np.where(y_test != y_pred)[0]
misclassified_cases = pd.DataFrame({'Actual': y_test[misclassified_idx], 'Predicted': y_pred[misclassified_idx]})
print("Misclassified Cases:\n", misclassified_cases)

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['Benign', 'Malignant'], yticklabels=['Benign', 'Malignant'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

# Plot ROC curve
from sklearn.metrics import roc_curve, auc
fpr, tpr, _ = roc_curve(y_test, y_prob)
roc_auc_score = auc(fpr, tpr)
plt.figure()
plt.plot(fpr, tpr, label='ROC curve (area = %0.2f)' % roc_auc_score)
plt.plot([0, 1], [0, 1], 'k--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
plt.show()

# Benchmark result
benchmark_result = {
    "task_id": "binary_classification_breast_cancer",
    "accuracy": accuracy,
    "f1": f1,
    "roc_auc": roc_auc,
    "baseline_accuracy": dummy_accuracy,
    "test_samples": len(y_test)
}

print("BENCHMARK_RESULT=", benchmark_result)

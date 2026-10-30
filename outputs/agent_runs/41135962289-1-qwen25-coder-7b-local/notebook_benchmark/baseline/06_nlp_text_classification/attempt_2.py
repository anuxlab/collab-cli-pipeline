import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# Define synthetic dataset
np.random.seed(42)
positive_texts = ["I love this product!", "Great service!", "Excellent experience!"]
negative_texts = ["Terrible product!", "Worst service ever!", "Awful experience!"]
texts = positive_texts * 10 + negative_texts * 10
labels = [1] * len(positive_texts) + [0] * len(negative_texts)

# Shuffle and split data
X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42, stratify=labels)

# Define pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('logreg', LogisticRegression())
])

# Train model
pipeline.fit(X_train, y_train)

# Predict
y_pred = pipeline.predict(X_test)

# Evaluate
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
report = classification_report(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)

# Baseline accuracy
baseline_accuracy = np.mean(y_test == 1)

# Misclassified count
misclassified_count = (y_test != y_pred).sum()

# Print results
print("Accuracy:", accuracy)
print("F1 Score:", f1)
print("Classification Report:\n", report)
print("Confusion Matrix:\n", conf_matrix)
print("Baseline Accuracy:", baseline_accuracy)
print("Misclassified Count:", misclassified_count)

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()

# BENCHMARK_RESULT={"task_id":"sentiment_classification","samples":40,"accuracy":accuracy,"f1":f1,"baseline_accuracy":baseline_accuracy,"misclassified_count":misclassified_count}

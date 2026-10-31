import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns

# Set random seed for reproducibility
np.random.seed(42)

# Create synthetic dataset
np.random.seed(42)
positive_texts = ["I love this product!", "This is the best!", "Absolutely fantastic!"]
negative_texts = ["I hate this product!", "This is terrible!", "Absolutely awful!"]
texts = positive_texts * 10 + negative_texts * 10
labels = [1] * len(positive_texts) + [0] * len(negative_texts)

# Shuffle the dataset
indices = np.arange(len(texts))
np.random.shuffle(indices)
texts = [texts[i] for i in indices]
labels = [labels[i] for i in indices]

# Split the dataset into training and test sets
X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42, stratify=labels)

# Create a pipeline with TfidfVectorizer and LogisticRegression
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('logreg', LogisticRegression(random_state=42))
])

# Train the pipeline
pipeline.fit(X_train, y_train)

# Make predictions
y_pred = pipeline.predict(X_test)

# Evaluate the model
report = classification_report(y_test, y_pred)
conf_matrix = confusion_matrix(y_test, y_pred)
accuracy = accuracy_score(y_test, y_pred)

# Print results
print("Classification Report:\n", report)
print("Confusion Matrix:\n", conf_matrix)
print("Accuracy:", accuracy)

# Baseline accuracy (majority class)
baseline_accuracy = np.mean(y_test == 1)

# Count misclassified samples
misclassified_count = (y_test != y_pred).sum()

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()

# Print benchmark result
BENCHMARK_RESULT = {
    "task_id": "sentiment_classification",
    "samples": len(texts),
    "accuracy": accuracy,
    "f1": report.split('\n')[3].split()[3],
    "baseline_accuracy": baseline_accuracy,
    "misclassified_count": misclassified_count
}
print("BENCHMARK_RESULT=", BENCHMARK_RESULT)

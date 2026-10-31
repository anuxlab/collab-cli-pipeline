import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Set random seed for reproducibility
np.random.seed(42)

# Create a synthetic dataset
texts = [
    "I love this product! It works perfectly.",
    "This is the worst experience I've ever had.",
    "I'm so happy with this service.",
    "I'm very disappointed with this product.",
    "This is the best thing I've ever bought.",
    "I'm extremely frustrated with this service.",
    "I'm thrilled with this product.",
    "I'm extremely unhappy with this product.",
    "I'm delighted with this service.",
    "I'm extremely dissatisfied with this product.",
    "I'm thrilled with this service.",
    "I'm extremely unhappy with this product.",
    "I'm delighted with this service.",
    "I'm extremely dissatisfied with this product.",
    "I'm thrilled with this service.",
    "I'm extremely unhappy with this product.",
    "I'm delighted with this service.",
    "I'm extremely dissatisfied with this product.",
    "I'm thrilled with this service.",
    "I'm extremely unhappy with this product.",
    "I'm delighted with this service.",
    "I'm extremely dissatisfied with this product.",
    "I'm thrilled with this service.",
    "I'm extremely unhappy with this product.",
    "I'm delighted with this service.",
    "I'm extremely dissatisfied with this product.",
    "I'm thrilled with this service.",
    "I'm extremely unhappy with this product.",
    "I'm delighted with this service.",
    "I'm extremely dissatisfied with this product.",
    "I'm thrilled with this service.",
    "I'm extremely unhappy with this product.",
    "I'm delighted with this service.",
    "I'm extremely dissatisfied with this product.",
    "I'm thrilled with this service.",
    "I'm extremely unhappy with this product.",
    "I'm delighted with this service.",
    "I'm extremely dissatisfied with this product."
]

labels = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0] * 3

# Convert to DataFrame
df = pd.DataFrame({'text': texts, 'label': labels})

# Split the dataset into training and test sets
X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label'])

# Define the pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LogisticRegression(random_state=42))
])

# Train the model
pipeline.fit(X_train, y_train)

# Predict on the test set
y_pred = pipeline.predict(X_test)

# Evaluate the model
report = classification_report(y_test, y_pred, output_dict=True)
conf_matrix = confusion_matrix(y_test, y_pred)

# Calculate accuracy and F1 score
accuracy = report['weighted avg']['precision']
f1 = report['weighted avg']['f1-score']

# Baseline accuracy (majority class)
baseline_accuracy = np.mean(y_test == 1)

# Count misclassified samples
misclassified_count = np.sum(y_test != y_pred)

# Plot confusion matrix
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['Negative', 'Positive'], yticklabels=['Negative', 'Positive'])
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()

# Print results
print(f"BENCHMARK_RESULT={{\"task_id\": \"sentiment_classification\", \"samples\": {len(df)}, \"accuracy\": {accuracy}, \"f1\": {f1}, \"baseline_accuracy\": {baseline_accuracy}, \"misclassified_count\": {misclassified_count}}}")

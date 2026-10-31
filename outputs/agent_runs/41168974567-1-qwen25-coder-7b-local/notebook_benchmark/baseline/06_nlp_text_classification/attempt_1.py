import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt

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

# Print results
print(f"Accuracy: {report['accuracy']}")
print(f"Precision: {report['precision']}")
print(f"Recall: {report['recall']}")
print(f"F1 Score: {report['f1-score']}")

# Plot the confusion matrix
plt.figure(figsize=(8, 6))
plt.imshow(conf_matrix, interpolation='nearest', cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.colorbar()
tick_marks = np.arange(2)
plt.xticks(tick_marks, ['Negative', 'Positive'], rotation=45)
plt.yticks(tick_marks, ['Negative', 'Positive'])
plt.xlabel('Predicted')
plt.ylabel('True')
plt.show()

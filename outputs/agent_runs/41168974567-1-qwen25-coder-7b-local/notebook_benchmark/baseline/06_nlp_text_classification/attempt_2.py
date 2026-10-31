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
    "I'm extremely dissatisfied with this product."
]

labels = [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]

# Ensure the lengths of texts and labels are the same
if len(texts) != len(labels):
    raise ValueError("The lengths of texts and labels must be the same")

# Create the DataFrame
df = pd.DataFrame({'text': texts, 'label': labels})

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(df['text'], df['label'], test_size=0.2, random_state=42)

# Create a pipeline with TfidfVectorizer and LogisticRegression
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LogisticRegression())
])

# Train the pipeline
pipeline.fit(X_train, y_train)

# Make predictions on the test set
y_pred = pipeline.predict(X_test)

# Evaluate the model
report = classification_report(y_test, y_pred)
print(report)

# Plot the confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)
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

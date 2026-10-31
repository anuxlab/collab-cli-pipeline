import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# Synthetic data creation
data = {
    'text': [
        "I love this product! It's amazing.",
        "This is the worst experience ever.",
        "Absolutely fantastic! Highly recommended.",
        "Terrible, do not buy!",
        "Absolutely thrilled with the service.",
        "Extremely disappointed with the quality.",
        "A+++++ would recommend.",
        "Horrible, would not purchase again.",
        "Absolutely delighted with the results.",
        "Completely dissatisfied with the performance.",
        "Absolutely amazing! 5 stars!",
        "Absolutely terrible, 1 star at most.",
        "Absolutely delighted with the service.",
        "Extremely unhappy with the price.",
        "Absolutely thrilled with the outcome.",
        "Horrible, would not recommend.",
        "Absolutely amazing! 5 stars!",
        "Absolutely terrible, 1 star at most.",
        "Absolutely delighted with the service.",
        "Extremely unhappy with the price.",
        "Absolutely thrilled with the outcome.",
        "Horrible, would not recommend.",
        "Absolutely amazing! 5 stars!",
        "Absolutely terrible, 1 star at most.",
        "Absolutely delighted with the service.",
        "Extremely unhappy with the price.",
        "Absolutely thrilled with the outcome.",
        "Horrible, would not recommend.",
        "Absolutely amazing! 5 stars!",
        "Absolutely terrible, 1 star at most."
    ],
    'sentiment': ['positive']*15 + ['negative']*15
}

df = pd.DataFrame(data)

# Stratified split
from sklearn.model_selection import train_test_split
df_train, df_test = train_test_split(df, test_size=0.2, stratify=df['sentiment'], random_state=42)

# Pipeline setup
pipeline = Pipeline([
    ('vectorizer', TfidfVectorizer()),
    ('classifier', LogisticRegression())
])

# Training
pipeline.fit(df_train['text'], df_train['sentiment'])

# Predictions
y_pred = pipeline.predict(df_test['text'])
y_true = df_test['sentiment']

# Metrics
accuracy = pipeline.score(df_test['text'], df_test['sentiment'])
precision = precision_score(y_true, y_pred, pos_label='positive')
recall = recall_score(y_true, y_pred, pos_label='positive')
f1 = f1_score(y_true, y_pred, pos_label='positive')
conf_matrix = confusion_matrix(y_true, y_pred)

# Misclassified texts
misclassified = df_test[y_pred != y_true]
misclassified_count = len(misclassified)

# Baseline: majority class
majority_class = df['sentiment'].mode()[0]
baseline_accuracy = (df['sentiment'] == majority_class).mean()

# Reporting
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1 Score: {f1:.4f}")
print("Confusion Matrix:\n", conf_matrix)
print("Misclassified texts count:", misclassified_count)

# Plotting
plt.figure(figsize=(8, 6))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', xticklabels=['negative', 'positive'], yticklabels=['negative', 'positive'])
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

# Synthetic data limitations and lexical shortcuts
print("Synthetic data limitations: The data is synthetic and lacks the complexity and diversity of real-world text data. It may not capture sarcasm, irony, or nuanced language use which are common in human communication.")
print("Lexical shortcuts: The model may rely on lexical shortcuts, such as positive or negative words, which can lead to over-simplified classifications. Real-world sentiment analysis often requires deeper semantic understanding.")

# Benchmark result
benchmark_result = {
    "task_id": "sentiment_analysis",
    "samples": len(df),
    "accuracy": accuracy,
    "f1": f1,
    "baseline_accuracy": baseline_accuracy,
    "misclassified_count": misclassified_count
}

print("BENCHMARK_RESULT=<JSON>", benchmark_result)


from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd
import joblib
import numpy as np


df = pd.read_csv("./datasets/train/motif_dataset_large.csv")  

print(f"Loaded {len(df)} samples with {df['label'].nunique()} classes")

train_texts, test_texts, train_labels, test_labels = train_test_split(
    df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
)

print("Loading sentence transformer model...")
encoder = SentenceTransformer("all-MiniLM-L6-v2")

print("Encoding training data...")
X_train = encoder.encode(train_texts.tolist(), show_progress_bar=True)
print("Encoding test data...")
X_test = encoder.encode(test_texts.tolist(), show_progress_bar=True)

print("Training Logistic Regression model...")
clf = LogisticRegression(max_iter=2000)
clf.fit(X_train, train_labels)

preds = clf.predict(X_test)
print("\nClassification Report:\n")
print(classification_report(test_labels, preds))

joblib.dump(clf, "./models/motif_classifier.pkl")
encoder.save("./models/motif_encoder")  
print("Model and encoder saved successfully!")

print("\nReloading model for testing...")
loaded_clf = joblib.load("./models/motif_classifier.pkl")
loaded_encoder = SentenceTransformer("motif_encoder")

test_inputs = [
    "Who made you?",
    "Where is the nearest police station?",
    "What time is it?",
    "Call an ambulance!",
    "Tell me about gravity",
    "Hey there!"
]

print("\nTesting loaded model:")
X_test_inputs = loaded_encoder.encode(test_inputs)
predictions = loaded_clf.predict(X_test_inputs)

for text, label in zip(test_inputs, predictions):
    print(f"Text: {text}\n → Predicted motif: {label}\n")


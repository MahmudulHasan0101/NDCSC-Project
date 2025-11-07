from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
import joblib
import numpy as np
import csv
import time

class TextClassifier:
    def __init__(self, encoder_path=None, clf_path=None):
        if encoder_path:
            self.encoder = SentenceTransformer(encoder_path)
        if clf_path:
            self.clf = joblib.load(clf_path)
    
    def predict(self, texts):
        single_input = False
        if isinstance(texts, str):
            single_input = True
            texts = [texts]
        
        X = self.encoder.encode(texts)
        preds = self.clf.predict(X)
        
        return preds[0] if single_input else preds


class InfoResponder:
    def __init__(self, csv_file):
        self.data = {}
        try:
            with open(csv_file, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        key, value = row[0].strip(), row[1].strip()
                        self.data[key.lower()] = value
        except FileNotFoundError:
            print(f"Error: File '{csv_file}' not found.")
        except Exception as e:
            print(f"Error reading CSV: {e}")

    def respond(self, query):
        query = query.lower()
        for key, value in self.data.items():
            if key in query:
                return f"{value}"
        return "404"


RESPONDERS = 
{
    "casual_botinfo"    : InfoResponder("./utils/casual_botinfo.csv"),
    "casual_smalltalk"  : InfoResponder("./utils/casual_smalltalk.csv"),
    "info_general"      : InfoResponder("./utils/info_general.csv"),
    "help_location"     : InfoResponder("./utils/help_location.csv"),
    "help_condition"    : InfoResponder("./utils/help_condition.csv"),
    "help_emergency"    : InfoResponder("./utils/help_emergency.csv")
}

MODEL = TextClassifier(encoder_path="./models/motif_encoder", clf_path="./models/motif_classifier.pkl")

def run(text : str):
    tp = MODEL.predict(text)
    response = RESPONDERS[tp].respond(text)
    return response


if __name__ == "__main__":
    import time
    
    texts = [
        "Who made you?",
        "Where is the nearest hospital?",
        "Hey there!"
    ]

    times = []
    predictions = []

    for t in texts:
        start = time.time()
        pred = MODEL.predict(t)
        end = time.time()

        predictions.append(pred)
        times.append(end - start)

    for t, p, elapsed in zip(texts, predictions, times):
        print(f"{t} → {p}  (time: {elapsed:.4f} s)")



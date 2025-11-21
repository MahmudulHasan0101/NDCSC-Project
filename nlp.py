from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sentence_transformers import SentenceTransformer
import joblib
import faiss
import numpy as np
import csv
import time

import browser


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
    def __init__(self, csv_file, encoder=None):
        self.keys = []
        self.data = {}
        self.encoder = encoder or SentenceTransformer("all-MiniLM-L6-v2")
        self.index = None

        try:
            with open(csv_file, newline='', encoding='utf-8') as f:
                import csv
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        key, value = row[0].strip(), row[1].strip()
                        key = key.lower()
                        self.keys.append(key)
                        self.data[key] = value

            if self.keys:
                embeddings = np.array(self.encoder.encode(self.keys), dtype='float32')
                self.index = faiss.IndexFlatL2(embeddings.shape[1])
                self.index.add(embeddings)
                self.embeddings = embeddings
        except FileNotFoundError:
            print(f"Error: File '{csv_file}' not found.")
        except Exception as e:
            print(f"Error reading CSV: {e}")

    def respond(self, query):
        if not self.index:
            return None

        q_vec = np.array([self.encoder.encode(query)], dtype='float32')
        D, I = self.index.search(q_vec, k=1)

        best_idx = I[0][0]
        best_key = self.keys[best_idx]
        return self.data[best_key]


def fn_casual_botinfo(text : str, response : str):
    return response

def fn_casual_smalltalk(text : str, response : str):
    return response

def fn_info_general(text : str, response : str):
    return response

def fn_help_location(text : str, response : str):
    # two cases: 1) user is trying to get to the nearest hospital/office etc, 2) asking location of a place by it's name

    # for case 1) we didn't impliment gps system, or planning to make bot depend on online, so we will just hard code it
    if "nearest" in text or "closest" in text:
        browser.open(f"https://www.google.com/search?q={text.replace(" ", "+")}")
    else:
        browser.open(f"{response.split(" ")[1]}")
    
    return response

def fn_help_condition(text : str, response : str):
    return response

def fn_help_emergency(text : str, response : str):
    return response


MODEL = TextClassifier(encoder_path="./models/motif_encoder", clf_path="./models/motif_classifier.pkl")

encoder = MODEL.encoder


RESPONDERS = {
    "casual_botinfo"    : InfoResponder("./utils/casual_smalltalk.csv", encoder),
    "casual_smalltalk"  : InfoResponder("./utils/casual_smalltalk.csv", encoder),
    "info_general"      : InfoResponder("./utils/help_location.csv", encoder),
    "help_location"     : InfoResponder("./utils/help_location.csv", encoder),
    "help_condition"    : InfoResponder("./utils/help_condition.csv", encoder),
    "help_emergency"    : InfoResponder("./utils/help_emergency.csv", encoder)
}


DISPATCHERS = {
    "casual_botinfo"    : fn_casual_botinfo,
    "casual_smalltalk"  : fn_casual_smalltalk,
    "info_general"      : fn_info_general,
    "help_location"     : fn_help_location,
    "help_condition"    : fn_help_condition,
    "help_emergency"    : fn_help_emergency
}

def run(text : str):
    tp = MODEL.predict(text)
    response = RESPONDERS[tp].respond(text)
    
    output = DISPATCHERS[tp](text, response)
    return output

def end():
    # cleanups to be defined
    pass


if __name__ == "__main__":
    import time
    
    texts = [
        "Who made you?",
        "where is Scholars International located",
        "Hey there!"
    ]

    times = []
    predictions = []

    for t in texts:
        start = time.time()
        pred = run(t)
        end = time.time()

        predictions.append(pred)
        times.append(end - start)

    for t, p, elapsed in zip(texts, predictions, times):
        print(f"{t} → {p}  (time: {elapsed:.4f} s)")





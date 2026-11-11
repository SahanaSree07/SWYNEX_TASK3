"""
Spam Email Classification (Spam vs Not Spam)
--------------------------------------------
Usage:
  python spam_classifier.py train                      # train + evaluate on data/emails.csv
  python spam_classifier.py train --data data/spam.csv # use a real dataset (Kaggle/UCI)
  python spam_classifier.py predict "Win a FREE prize now!!!"
  python spam_classifier.py interactive                # type emails, get predictions

Dataset formats accepted (auto-detected):
  - columns: label,text           (label = spam/ham or 1/0)
  - columns: v1,v2                (Kaggle/UCI "spam.csv", latin-1 encoded)
"""
import argparse
import re
import sys

import joblib
import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

MODEL_PATH = "spam_model.joblib"


def clean_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"http\S+|www\.\S+", " url ", text)   # keep a "url" signal
    text = re.sub(r"\d+", " num ", text)                  # numbers -> token
    text = re.sub(r"[^a-z\s]", " ", text)                 # drop punctuation
    return re.sub(r"\s+", " ", text).strip()


def load_data(path: str, clean: bool = True) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")
    cols = {c.lower(): c for c in df.columns}
    if "label" in cols and "text" in cols:
        df = df[[cols["label"], cols["text"]]]
    elif "v1" in cols and "v2" in cols:
        df = df[[cols["v1"], cols["v2"]]]
    else:
        sys.exit("CSV must have columns (label,text) or (v1,v2).")
    df.columns = ["label", "text"]
    df = df.dropna().drop_duplicates()
    df["label"] = df["label"].astype(str).str.lower().map(
        {"spam": 1, "ham": 0, "1": 1, "0": 0, "not spam": 0}
    )
    df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)
    if clean:
        df["text"] = df["text"].map(clean_text)
    return df


def make_pipeline(model):
    return Pipeline([
        ("tfidf", TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1)),
        ("clf", model),
    ])


def evaluate(name, pipe, X_test, y_test):
    pred = pipe.predict(X_test)
    metrics = {
        "model": name,
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "f1": f1_score(y_test, pred),
    }
    print(f"\n=== {name} ===")
    print(classification_report(y_test, pred, target_names=["Not Spam", "Spam"]))
    print("Confusion matrix [[TN FP] [FN TP]]:\n", confusion_matrix(y_test, pred))
    return metrics, pred


def train(data_path: str):
    df = load_data(data_path)
    print(f"Loaded {len(df)} emails | spam: {df.label.sum()} | not spam: {(df.label == 0).sum()}")

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    candidates = {
        "Multinomial Naive Bayes": make_pipeline(MultinomialNB(alpha=0.5)),
        "Logistic Regression": make_pipeline(LogisticRegression(max_iter=1000, class_weight="balanced")),
    }

    results, preds = [], {}
    for name, pipe in candidates.items():
        pipe.fit(X_train, y_train)
        m, p = evaluate(name, pipe, X_test, y_test)
        results.append(m)
        preds[name] = p

    table = pd.DataFrame(results).set_index("model").round(4)
    print("\n=== Model comparison ===\n", table)
    table.to_csv("results.csv")

    # Pick best model by precision first (false positives are costly), then F1
    best_name = table.sort_values(["precision", "f1"], ascending=False).index[0]
    best = candidates[best_name]
    print(f"\nSelected model: {best_name}")

    ConfusionMatrixDisplay.from_predictions(
        y_test, preds[best_name], display_labels=["Not Spam", "Spam"], cmap="Blues"
    )
    plt.title(f"Confusion Matrix - {best_name}")
    plt.savefig("confusion_matrix.png", dpi=150, bbox_inches="tight")

    joblib.dump(best, MODEL_PATH)
    print(f"Saved model -> {MODEL_PATH}, results.csv, confusion_matrix.png")


def predict_text(text: str):
    try:
        model = joblib.load(MODEL_PATH)
    except FileNotFoundError:
        sys.exit("No trained model found. Run: python spam_classifier.py train")
    cleaned = clean_text(text)
    proba = model.predict_proba([cleaned])[0][1]
    label = "SPAM" if proba >= 0.5 else "NOT SPAM"
    return label, proba


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["train", "predict", "interactive"])
    ap.add_argument("text", nargs="?", default="")
    ap.add_argument("--data", default="data/emails.csv")
    args = ap.parse_args()

    if args.mode == "train":
        train(args.data)
    elif args.mode == "predict":
        label, p = predict_text(args.text)
        print(f"{label} (spam probability: {p:.2%})")
    else:
        print("Type an email (blank line to quit).")
        while True:
            t = input("> ").strip()
            if not t:
                break
            label, p = predict_text(t)
            print(f"  {label} (spam probability: {p:.2%})")


if __name__ == "__main__":
    main()

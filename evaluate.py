"""Evaluates both models and collects their failure cases.

Two test sets:
  1. The held-out 20% of the SMS Spam Collection (the same split used for training in Task 1).
  2. eval_cases.csv, a small hand-written set of tricky messages (phishing, real bank alerts, OTPs...).

Usage:
    python evaluate.py                          # needs data/spam.csv and spam_model.joblib
    python evaluate.py --data data/emails.csv   # use another dataset
    python evaluate.py --skip-pretrained        # Naive Bayes only (no Hugging Face download)

Writes evaluation_results.json (used by the app), evaluation_report.md and failure_cases.csv.
"""
import argparse
import json
import os
import sys

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

import hf_spam
from spam_classifier import MODEL_PATH, clean_text, load_data

MAX_FAILURES = 15   # per model per test set, in the JSON file and the report


def metrics(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
    }


def failures(texts, y_true, probs, categories=None):
    rows = []
    for i, (t, y, p) in enumerate(zip(texts, y_true, probs)):
        pred = int(p >= 0.5)
        if pred != int(y):
            rows.append({
                "text": t if len(t) <= 160 else t[:157] + "...",
                "truth": "SPAM" if y else "NOT SPAM",
                "predicted": "SPAM" if pred else "NOT SPAM",
                "spam_prob": round(float(p), 4),
                "kind": "missed spam" if y else "false alarm",
                "category": categories[i] if categories is not None else "",
            })
    rows.sort(key=lambda r: -abs(r["spam_prob"] - 0.5))   # most confident mistakes first
    return rows


def run_models(raw_texts, nb_model, use_pretrained):
    """Return {"naive_bayes": [probs], "pretrained": [probs] or None}."""
    out = {"naive_bayes": list(nb_model.predict_proba([clean_text(t) for t in raw_texts])[:, 1]), "pretrained": None}
    if use_pretrained:
        print(f"  running the pretrained model ({hf_spam.MODEL_ID}) on {len(raw_texts)} messages...")
        out["pretrained"] = [p for _, p, _ in hf_spam.predict_many(raw_texts)]
    return out


def evaluate_set(name, raw_texts, labels, nb_model, use_pretrained, categories=None):
    probs = run_models(list(raw_texts), nb_model, use_pretrained)
    result = {"size": len(labels), "spam": int(sum(labels)), "models": {}}
    for key, p in probs.items():
        if p is None:
            continue
        preds = [int(x >= 0.5) for x in p]
        m = metrics(labels, preds)
        m["failure_count"] = m["fp"] + m["fn"]
        m["failures"] = failures(list(raw_texts), labels, p, categories)[:MAX_FAILURES]
        result["models"][key] = m
        print(f"  {name} | {key}: accuracy {m['accuracy']:.1%}, precision {m['precision']:.1%}, recall {m['recall']:.1%}, F1 {m['f1']:.1%}")
    return result


def write_report(results):
    names = {"naive_bayes": "Naive Bayes (ours)", "pretrained": f"Pretrained ({results['pretrained_model']})"}
    lines = ["# Evaluation report", ""]
    for key, title in (("test_set", "Test set: held-out SMS messages"), ("stress_set", "Stress set: hand-written tricky messages")):
        block = results.get(key)
        if not block:
            continue
        lines += [f"## {title}", "", f"{block['size']} messages ({block['spam']} spam).", "",
                  "| Model | Accuracy | Precision | Recall | F1 | Missed spam | False alarms |", "|---|---|---|---|---|---|---|"]
        for mk, m in block["models"].items():
            lines.append(f"| {names[mk]} | {m['accuracy']:.1%} | {m['precision']:.1%} | {m['recall']:.1%} | {m['f1']:.1%} | {m['fn']} | {m['fp']} |")
        lines.append("")
        for mk, m in block["models"].items():
            lines += [f"### Failure cases: {names[mk]} ({m['failure_count']} total, most confident mistakes first)", ""]
            if not m["failures"]:
                lines += ["None.", ""]
                continue
            lines += ["| Kind | Message | Spam probability |", "|---|---|---|"]
            for f in m["failures"]:
                lines.append(f"| {f['kind']} | {f['text'].replace('|', '/')} | {f['spam_prob']:.1%} |")
            lines.append("")
    lines += ["## Caveats", "",
              "- The stress set is small and hand-written. It shows where the models differ, not how they perform in general.",
              "- The pretrained model's training data is not fully known to us, so it may have seen the SMS test messages. Treat its test-set scores as optimistic.", ""]
    with open("evaluation_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/spam.csv")
    ap.add_argument("--cases", default="eval_cases.csv")
    ap.add_argument("--skip-pretrained", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(MODEL_PATH):
        sys.exit(f"{MODEL_PATH} not found. Train first: python spam_classifier.py train --data {args.data}")
    nb_model = joblib.load(MODEL_PATH)

    use_pretrained = not args.skip_pretrained
    if use_pretrained:
        try:
            hf_spam.load()
        except Exception as exc:
            print(f"Could not load the pretrained model ({type(exc).__name__}: {exc}). Continuing with Naive Bayes only.")
            use_pretrained = False

    results = {"pretrained_model": hf_spam.MODEL_ID if use_pretrained else None}
    all_failures = []

    if os.path.exists(args.data):
        print("Test set (held-out split of", args.data + ")")
        df = load_data(args.data, clean=False)
        _, X_test, _, y_test = train_test_split(df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"])
        results["test_set"] = evaluate_set("test set", X_test.tolist(), y_test.tolist(), nb_model, use_pretrained)
    else:
        print(f"Skipping the test set: {args.data} not found. Run python download_data.py first.")

    if os.path.exists(args.cases):
        print("Stress set (" + args.cases + ")")
        cases = pd.read_csv(args.cases)
        labels = (cases["label"].str.lower() == "spam").astype(int).tolist()
        results["stress_set"] = evaluate_set("stress set", cases["text"].tolist(), labels, nb_model, use_pretrained, cases["category"].tolist())

    for set_name in ("test_set", "stress_set"):
        for mk, m in results.get(set_name, {}).get("models", {}).items():
            for f in m["failures"]:
                all_failures.append({"set": set_name, "model": mk, **f})

    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    pd.DataFrame(all_failures).to_csv("failure_cases.csv", index=False)
    write_report(results)
    print("\nSaved evaluation_results.json, evaluation_report.md and failure_cases.csv")


if __name__ == "__main__":
    main()

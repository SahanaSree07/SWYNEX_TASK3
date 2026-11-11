"""Runs both models on examples.csv and saves example inputs/outputs.

Usage:  python compare.py
        python compare.py "your own message here"
"""
import sys

import pandas as pd

import hf_spam
from spam_classifier import predict_text


def run_both(text):
    nb_label, nb_p = predict_text(text)
    try:
        hf_label, hf_p, raw = hf_spam.predict(text)
    except Exception as e:  # keep going so you still see the Naive Bayes result
        print("  (Hugging Face model unavailable:", e, ")")
        hf_label, hf_p = "N/A", float("nan")
    return nb_label, nb_p, hf_label, hf_p


if len(sys.argv) > 1:
    texts = [" ".join(sys.argv[1:])]
else:
    texts = pd.read_csv("examples.csv")["text"].tolist()

rows = []
for t in texts:
    nb_label, nb_p, hf_label, hf_p = run_both(t)
    rows.append({
        "input": t,
        "naive_bayes": nb_label, "nb_spam_prob": round(nb_p, 4),
        "huggingface": hf_label, "hf_spam_prob": round(hf_p, 4),
        "agree": nb_label == hf_label,
    })
    print(f"\nINPUT: {t}\n  Naive Bayes : {nb_label} ({nb_p:.1%})\n  Hugging Face: {hf_label} ({hf_p:.1%})")

df = pd.DataFrame(rows)
if len(sys.argv) == 1:
    df.to_csv("examples_output.csv", index=False)
    with open("examples_output.md", "w", encoding="utf-8") as f:
        f.write("| Input | Naive Bayes | Hugging Face |\n|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['input']} | {r['naive_bayes']} ({r['nb_spam_prob']:.1%}) | "
                    f"{r['huggingface']} ({r['hf_spam_prob']:.1%}) |\n")
    print("\nSaved examples_output.csv and examples_output.md")

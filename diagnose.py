"""Shows what a Hugging Face model really outputs, so we can check its labels.

Usage:  python diagnose.py                                   (tests the default model)
        python diagnose.py typeform/distilbert-base-uncased-mnli
"""
import sys

from transformers import pipeline

model_id = sys.argv[1] if len(sys.argv) > 1 else "mrm8488/bert-tiny-finetuned-sms-spam-detection"
tests = [
    "Congratulations! You won a free prize, click http://claim.biz now",
    "URGENT! Your account is suspended, send your bank details to verify",
    "WINNER!! As a valued network customer you have been selected to receive a 900 prize reward. Call now",
    "Hi, can you send me the DBMS assignment notes before the lab tomorrow?",
    "Are we still meeting for the project discussion at 4 pm?",
]

print("Model:", model_id)
if "mnli" in model_id.lower():
    p = pipeline("zero-shot-classification", model=model_id)
    for t in tests:
        out = p(t, candidate_labels=["a spam or scam message", "a normal personal or work message"],
                hypothesis_template="This message is {}.")
        print(f"\n{t}\n  {list(zip(out['labels'], [round(s, 3) for s in out['scores']]))}")
else:
    p = pipeline("text-classification", model=model_id, truncation=True, max_length=128)
    print("Label names in the model config:", p.model.config.id2label)
    for t in tests:
        print(f"\n{t}\n  {p(t, top_k=None)}")

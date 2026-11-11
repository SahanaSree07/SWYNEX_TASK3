"""Pretrained Hugging Face spam detector (no API key needed).

Default: mshenoda/roberta-spam, a RoBERTa spam classifier (LABEL_1 = spam, LABEL_0 = not spam). Change it with an environment variable
(PowerShell):  $env:HF_SPAM_MODEL = "some-user/some-model"

Model ids that contain "mnli" (for example typeform/distilbert-base-uncased-mnli) run as a
zero-shot classifier: no spam labels needed, the model scores "a spam or scam message"
against "a normal message".
"""
import os

MODEL_ID = os.environ.get("HF_SPAM_MODEL", "mshenoda/roberta-spam")
SPAM_LABELS = {"LABEL_1", "SPAM", "1"}   # every other label is treated as Not Spam
ZERO_SHOT = "mnli" in MODEL_ID.lower()
ZS_SPAM = "a spam or scam message"
ZS_HAM = "a normal personal or work message"

_pipe = None


def load():
    """Load the model once (first call downloads it)."""
    global _pipe
    if _pipe is None:
        from transformers import pipeline  # imported here so other code runs without it
        if ZERO_SHOT:
            _pipe = pipeline("zero-shot-classification", model=MODEL_ID)
        else:
            _pipe = pipeline("text-classification", model=MODEL_ID, truncation=True, max_length=128)
    return _pipe


def predict(text: str):
    """Return (label, spam_probability, raw_label)."""
    pipe = load()
    if ZERO_SHOT:
        out = pipe(text, candidate_labels=[ZS_SPAM, ZS_HAM], hypothesis_template="This message is {}.")
        p_spam = float(dict(zip(out["labels"], out["scores"]))[ZS_SPAM])
        raw = out["labels"][0]
    else:
        out = pipe(text)[0]
        raw = str(out["label"])
        score = float(out["score"])
        p_spam = score if raw.upper() in SPAM_LABELS else 1.0 - score
    return ("SPAM" if p_spam >= 0.5 else "NOT SPAM"), p_spam, raw


def predict_many(texts, batch_size: int = 16):
    """Predict a list of messages at once. Returns a list of (label, spam_probability, raw_label)."""
    texts = list(texts)
    if ZERO_SHOT:
        return [predict(t) for t in texts]
    outs = load()(texts, batch_size=batch_size)
    results = []
    for out in outs:
        raw = str(out["label"])
        score = float(out["score"])
        p_spam = score if raw.upper() in SPAM_LABELS else 1.0 - score
        results.append(("SPAM" if p_spam >= 0.5 else "NOT SPAM", p_spam, raw))
    return results

"""Spam check web app with a combined decision, explanations, input checks and evaluation results.

Run:  python server.py     then open http://127.0.0.1:5000
No API keys are used. The pretrained model downloads from Hugging Face on first start.
"""
import json
import logging
import os
import threading
import webbrowser

import joblib
import pandas as pd
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

import hf_spam
from explain import explain_nb
from spam_classifier import MODEL_PATH, predict_text
from triage import triage
from validation import InputError, validate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("spamcheck")

app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024   # reject huge requests

hf_state = {"status": "loading", "error": None}
hf_done = threading.Event()   # set once the pretrained model finished loading (or failed)
_nb_model = None


def get_nb():
    """Load the Naive Bayes model once. Returns None if it has not been trained yet."""
    global _nb_model
    if _nb_model is None and os.path.exists(MODEL_PATH):
        _nb_model = joblib.load(MODEL_PATH)
    return _nb_model


def _warm_up():
    """Load the pretrained model in the background so the page opens instantly."""
    try:
        hf_spam.load()
        hf_state["status"] = "ready"
    except Exception as exc:  # missing package, no internet on first run, etc.
        hf_state["status"] = "error"
        hf_state["error"] = f"{type(exc).__name__}: {exc}"
        log.warning("Pretrained model failed to load: %s", hf_state["error"])
    finally:
        hf_done.set()


threading.Thread(target=_warm_up, daemon=True).start()


def error(message, code, status):
    return jsonify({"error": message, "code": code}), status


@app.errorhandler(404)
def not_found(_):
    return error("Page not found.", "not_found", 404)


@app.errorhandler(413)
def too_large(_):
    return error("That request is too large. Send a shorter message.", "too_large", 413)


@app.errorhandler(Exception)
def unexpected(exc):
    if isinstance(exc, HTTPException):          # 405 and similar: keep the real status code
        return error(exc.description, "http_error", exc.code)
    log.exception("Unexpected error")
    return error("Something went wrong on the server. Try again, and check the PowerShell window for details.", "server_error", 500)


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/status")
def status():
    nb_ready = get_nb() is not None
    return jsonify({
        "nb": {"status": "ready" if nb_ready else "error",
               "error": None if nb_ready else "spam_model.joblib not found. Run: python spam_classifier.py train --data data/spam.csv"},
        "hf": {**hf_state, "model": hf_spam.MODEL_ID},
    })


@app.post("/api/predict")
def predict():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error("Send the message as JSON, like {\"text\": \"...\"}.", "bad_request", 400)
    try:
        text, warnings = validate(body.get("text"))
    except InputError as exc:
        return error(str(exc), "invalid_input", 400)

    nb_model = get_nb()
    explanation = None
    if nb_model is not None:
        try:
            label, prob = predict_text(text)
            nb = {"label": label, "prob": float(prob)}
            explanation = explain_nb(nb_model, text)
        except Exception as exc:
            log.exception("Naive Bayes failed")
            nb = {"error": f"{type(exc).__name__}: {exc}"}
    else:
        nb = {"error": "Naive Bayes model not found. Train it first."}

    if hf_state["status"] == "loading":
        hf_done.wait(timeout=180)   # first request waits for the model instead of failing
    if hf_state["status"] == "ready":
        try:
            label, prob, _raw = hf_spam.predict(text)
            hf = {"label": label, "prob": float(prob)}
        except Exception as exc:
            log.exception("Pretrained model failed")
            hf = {"error": f"{type(exc).__name__}: {exc}"}
    elif hf_state["status"] == "loading":
        hf = {"error": "Still loading. Try again in a moment."}
    else:
        hf = {"error": hf_state["error"] or "Pretrained model unavailable."}

    return jsonify({"nb": nb, "hf": hf, "triage": triage(nb, hf),
                    "explanation": explanation, "warnings": warnings})


@app.get("/api/metrics")
def metrics():
    """Task 1 test-set results for our Naive Bayes model (from results.csv)."""
    if not os.path.exists("results.csv"):
        return jsonify({})
    df = pd.read_csv("results.csv").set_index("model")
    if "Multinomial Naive Bayes" not in df.index:
        return jsonify({})
    row = df.loc["Multinomial Naive Bayes"]
    return jsonify({k: float(row[k]) for k in ("accuracy", "precision", "recall", "f1") if k in row})


@app.get("/api/evaluation")
def evaluation():
    """Results written by evaluate.py (metrics and failure cases for both models)."""
    if not os.path.exists("evaluation_results.json"):
        return jsonify({})
    try:
        with open("evaluation_results.json", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except (OSError, ValueError):
        log.exception("Could not read evaluation_results.json")
        return error("The evaluation file could not be read. Run python evaluate.py again.", "bad_evaluation_file", 500)


if __name__ == "__main__":
    url = "http://127.0.0.1:5000"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print(f"\nSpam check is running at {url}  (press Ctrl+C to stop)\n")
    app.run(host="127.0.0.1", port=5000, debug=False)

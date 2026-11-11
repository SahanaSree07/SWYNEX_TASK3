"""Combines the two models into one decision and flags messages a person should review."""

UNSURE_LOW = 0.35
UNSURE_HIGH = 0.65


def _ok(r):
    return bool(r) and "error" not in r


def _unsure(r):
    return UNSURE_LOW <= r["prob"] <= UNSURE_HIGH


def triage(nb, hf):
    """nb and hf are dicts like {"label": "SPAM", "prob": 0.97} or {"error": "..."}.

    Returns {"decision", "level", "reason"}; level is one of spam, safe, review, error.
    """
    results = [r for r in (nb, hf) if _ok(r)]
    if not results:
        return {"decision": "NO RESULT", "level": "error",
                "reason": "Neither model could produce a result. Check the status chips at the top of the page."}

    if len(results) == 1:
        r = results[0]
        who = "Naive Bayes" if r is nb else "The pretrained model"
        if _unsure(r):
            return {"decision": "NEEDS REVIEW", "level": "review",
                    "reason": f"Only {who} is available and it is unsure ({r['prob']:.0%} spam). A person should check this message."}
        spam = r["label"] == "SPAM"
        return {"decision": "LIKELY SPAM" if spam else "LIKELY NOT SPAM", "level": "spam" if spam else "safe",
                "reason": f"Based on {who} only, because the other model is not available."}

    if nb["label"] != hf["label"]:
        return {"decision": "NEEDS REVIEW", "level": "review",
                "reason": "The two models disagree. A person should check this message."}
    if _unsure(nb) or _unsure(hf):
        return {"decision": "NEEDS REVIEW", "level": "review",
                "reason": "Both models lean the same way, but at least one is unsure. A person should check this message."}
    spam = nb["label"] == "SPAM"
    return {"decision": "LIKELY SPAM" if spam else "LIKELY NOT SPAM", "level": "spam" if spam else "safe",
            "reason": "Both models agree and both are confident."}

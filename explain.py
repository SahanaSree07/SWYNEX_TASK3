"""Shows which words pushed the Naive Bayes model toward spam or toward not spam."""
from spam_classifier import clean_text


def explain_nb(model, text, top=5):
    """Return {"spam_words": [...], "safe_words": [...]} or None if the model type is not supported."""
    tfidf = model.named_steps["tfidf"]
    clf = model.named_steps["clf"]
    if hasattr(clf, "feature_log_prob_"):          # Naive Bayes
        weights = clf.feature_log_prob_[1] - clf.feature_log_prob_[0]
    elif hasattr(clf, "coef_"):                    # Logistic Regression
        weights = clf.coef_[0]
    else:
        return None

    X = tfidf.transform([clean_text(text)]).tocoo()
    names = tfidf.get_feature_names_out()
    contribs = [(str(names[j]), float(v * weights[j])) for j, v in zip(X.col, X.data)]
    spam = sorted((c for c in contribs if c[1] > 0), key=lambda c: -c[1])[:top]
    safe = sorted((c for c in contribs if c[1] < 0), key=lambda c: c[1])[:top]
    fmt = lambda rows: [{"word": w, "weight": round(s, 3)} for w, s in rows]
    return {"spam_words": fmt(spam), "safe_words": fmt(safe)}

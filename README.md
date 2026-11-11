# SWYNEX Task 3: Intelligent Feature (Spam Detection)

Builds on Task 2 (a Naive Bayes model plus a pretrained Hugging Face model). Task 3 adds an intelligent decision layer, explanations, error handling, and a proper evaluation with failure cases.

## What is new
| Feature | What it does | Where |
|---|---|---|
| **Combined decision with review flag** | Merges both models into one result: `LIKELY SPAM`, `LIKELY NOT SPAM`, or `NEEDS REVIEW` when the models disagree or either one is unsure (35% to 65% spam). If one model is down, it uses the other and says so. | `triage.py` |
| **Explanation** | Shows which words pushed the Naive Bayes model toward spam or toward not spam. | `explain.py` |
| **Input checks and error handling** | Rejects empty, too-short, or letterless input with a clear message. Warns about non-English text, very short messages, and messages over 5000 characters. JSON errors with codes for bad requests, large requests, and server faults. If the pretrained model fails to load, the app keeps working with Naive Bayes only. | `validation.py`, `server.py` |
| **Evaluation with failure cases** | Scores both models on the held-out SMS test set and on a hand-written stress set (`eval_cases.csv`: 30 messages including phishing, real bank alerts and one-time codes), and lists every model's mistakes, most confident first. | `evaluate.py` |
| **Interface** | The web app shows the decision, the explanation, warnings, a session table, and the evaluation tables and failure cases. | `static/` |
| **Tests** | 14 unit tests for the input checks and the decision logic. | `tests/` |

## Setup and run
```
pip install -r requirements.txt
python download_data.py
python spam_classifier.py train --data data/spam.csv     # creates spam_model.joblib and results.csv
python evaluate.py                                       # creates evaluation_results.json, evaluation_report.md, failure_cases.csv
python server.py                                         # opens http://127.0.0.1:5000
python -m unittest discover -s tests -v                  # run the tests
```
`python evaluate.py --skip-pretrained` evaluates Naive Bayes only (no Hugging Face download).

No API key is used anywhere in this project, so there are no secrets in the code or the repository.

## How the decision works
| Naive Bayes | Pretrained | Decision |
|---|---|---|
| Spam, confident | Spam, confident | Likely spam |
| Not spam, confident | Not spam, confident | Likely not spam |
| Different answers | | Needs review |
| Either one between 35% and 65% | | Needs review |
| Only one model available | | That model's answer, with a note (or Needs review if unsure) |

## Error handling
| Situation | Behaviour |
|---|---|
| Empty message, fewer than 3 characters, or no letters | 400 error with a plain-language message, shown under the text box |
| Message over 5000 characters | Cut to 5000 characters, with a warning |
| Not English | Warning that results may be unreliable |
| Pretrained model missing or still loading | First request waits for it; if it fails, the page shows Naive Bayes only |
| Naive Bayes model not trained | Status chip shows "model file missing"; the pretrained model still works |
| Invalid JSON, wrong method, oversized request, unknown page | JSON error with a code (`bad_request`, `http_error`, `too_large`, `not_found`) |
| Unexpected crash in a model | Logged on the server; the page shows a message instead of breaking |

## Evaluation
Results from running `python evaluate.py` are saved as `evaluation_report.md` (readable report), `evaluation_results.json` (used by the app), and `failure_cases.csv` (every mistake).

**Caveats**
- The stress set is small (30 messages) and hand-written. It shows where the models differ, not how they perform in general.
- The pretrained model's training data is not fully known to us, so it may have seen the SMS test messages. Treat its test-set scores as optimistic.
- Both models learned from short English text messages. Long emails, other languages, and new scam styles can be missed.

## Project files
- `server.py`: Flask backend (`/api/predict`, `/api/status`, `/api/metrics`, `/api/evaluation`)
- `static/`: frontend (`index.html`, `style.css`, `app.js`)
- `triage.py`, `explain.py`, `validation.py`: the new features
- `evaluate.py`, `eval_cases.csv`: evaluation
- `hf_spam.py`: pretrained model (`mshenoda/roberta-spam`); `spam_classifier.py`: Task 1 model code
- `compare.py`, `examples.csv`: command-line comparison from Task 2

"""Run with:  python -m unittest discover -s tests -v   (from the project folder)"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from triage import triage          # noqa: E402
from validation import InputError, MAX_LEN, validate   # noqa: E402


def r(label, prob):
    return {"label": label, "prob": prob}


class ValidationTests(unittest.TestCase):
    def test_empty_message_is_rejected(self):
        for bad in ("", "   ", None):
            with self.assertRaises(InputError):
                validate(bad)

    def test_non_text_is_rejected(self):
        with self.assertRaises(InputError):
            validate(12345)

    def test_too_short_is_rejected(self):
        with self.assertRaises(InputError):
            validate("hi")

    def test_no_letters_is_rejected(self):
        with self.assertRaises(InputError):
            validate("12345 67890 !!!")

    def test_long_message_is_cut_with_a_warning(self):
        text, warnings = validate("free prize " * 1000)
        self.assertEqual(len(text), MAX_LEN)
        self.assertTrue(any("longer than" in w for w in warnings))

    def test_non_english_gets_a_warning(self):
        _, warnings = validate("வணக்கம் நண்பா எப்படி இருக்கிறீர்கள் இன்று")
        self.assertTrue(any("English" in w for w in warnings))

    def test_normal_message_has_no_warnings(self):
        text, warnings = validate("Hi, can you send me the DBMS notes before the lab?")
        self.assertEqual(warnings, [])


class TriageTests(unittest.TestCase):
    def test_both_confident_spam(self):
        self.assertEqual(triage(r("SPAM", 0.95), r("SPAM", 1.0))["level"], "spam")

    def test_both_confident_safe(self):
        self.assertEqual(triage(r("NOT SPAM", 0.02), r("NOT SPAM", 0.0))["level"], "safe")

    def test_disagreement_needs_review(self):
        self.assertEqual(triage(r("NOT SPAM", 0.27), r("SPAM", 1.0))["level"], "review")

    def test_agreement_but_unsure_needs_review(self):
        self.assertEqual(triage(r("SPAM", 0.55), r("SPAM", 0.99))["level"], "review")

    def test_one_model_down_uses_the_other(self):
        out = triage(r("SPAM", 0.97), {"error": "not loaded"})
        self.assertEqual(out["level"], "spam")
        self.assertIn("Naive Bayes", out["reason"])

    def test_one_model_down_and_unsure_needs_review(self):
        self.assertEqual(triage({"error": "x"}, r("SPAM", 0.5))["level"], "review")

    def test_both_models_down(self):
        self.assertEqual(triage({"error": "a"}, {"error": "b"})["level"], "error")


if __name__ == "__main__":
    unittest.main()

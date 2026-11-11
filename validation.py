"""Input checks. Bad input gets a clear message instead of a crash or a silent wrong answer."""

MAX_LEN = 5000
MIN_LEN = 3


class InputError(ValueError):
    """The message cannot be checked. The text is safe to show to the user."""


def validate(text):
    """Return (cleaned_text, warnings). Raises InputError when the message cannot be checked."""
    if not isinstance(text, str):
        raise InputError("The message must be text.")
    t = text.strip()
    if not t:
        raise InputError("Enter a message first.")
    if len(t) < MIN_LEN:
        raise InputError(f"That message is too short to judge. Enter at least {MIN_LEN} characters.")
    letters = [c for c in t if c.isalpha()]
    if not letters:
        raise InputError("The message has no letters in it. Enter an email or text message.")

    warnings = []
    if len(t) > MAX_LEN:
        t = t[:MAX_LEN]
        warnings.append(f"The message was longer than {MAX_LEN} characters, so only the first {MAX_LEN} were checked.")
    letters = [c for c in t if c.isalpha()]
    if letters and sum(c.isascii() for c in letters) / len(letters) < 0.6:
        warnings.append("This message does not look like English. Both models learned from English text, so the result may be unreliable.")
    if len(t.split()) < 4:
        warnings.append("Very short messages give less reliable results.")
    return t, warnings

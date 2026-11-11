"""Downloads the SMS Spam Collection and saves it as data/spam.csv (label,text)."""
import csv, io, os, urllib.request, zipfile

URLS = [
    ("tsv", "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv"),
    ("zip", "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip"),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read()

rows = None
for kind, url in URLS:
    try:
        raw = fetch(url)
        if kind == "zip":
            z = zipfile.ZipFile(io.BytesIO(raw))
            raw = z.read("SMSSpamCollection")
        text = raw.decode("utf-8", errors="replace")
        rows = [ln.split("\t", 1) for ln in text.splitlines() if "\t" in ln]
        if len(rows) > 1000:
            print("Downloaded from", url)
            break
    except Exception as e:
        print("Failed:", url, "->", e)
        rows = None

if not rows:
    raise SystemExit("Could not download. Download spam.csv manually from Kaggle into the data folder.")

os.makedirs("data", exist_ok=True)
with open("data/spam.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["label", "text"])
    w.writerows(rows)
print(f"Saved data/spam.csv with {len(rows)} messages")

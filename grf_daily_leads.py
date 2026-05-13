import os, json, datetime, smtplib, requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GOOGLE_API_KEY  = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CX       = os.environ.get("GOOGLE_CX")
GROQ_API_KEY    = os.environ.get("GROQ_API_KEY")
EMAIL_SENDER    = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD  = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECIPIENT = "nimrodb@grofitseeds.com"

SEARCH_QUERIES = [
    "ornamental flower seed wholesale distributor importer Netherlands Germany France",
    "cut flower seed distributor importer wholesale USA Canada ornamental sunflower",
    "flower seed importer distributor Vietnam Thailand wholesale ornamental commercial",
    "semillas flores distribuidor mayorista girasol ornamental Espana profesional",
    "sementi fiori distributore grossista girasole ornamentale professionale Italia",
    "ornamental sunflower seed importer distributor wholesale professional grower",
]

def search_google(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query, "num": 8}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return [{"title": i.get("title",""), "link": i.get("link",""), "snippet": i.get("snippet","")} for i in r.json().get("items", [])]

def analyze_leads(results):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""You are a lead generation expert for Grofit Flower Seeds (GRF).
Find ONLY flower seed distributors or large commercial cut flower growers.
EXCLUDE: breeders, crop protection companies, food seed companies, home gardeners retailers.
Search results: {json.dumps(results, ensure_ascii=False)}
Extract: Company, Contact, Title, Email, Phone, Website, Country, Reason.
Format: Markdown table."""
    body = {"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 2000}
    r = requests.post(url, headers=headers, json=body, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]

def send_email(subject, body):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECIPIENT
    html = f"<html><body style='font-family:Arial'><h2>GRF — לידים יומיים</h2><pre>{body}</pre></body></html>"
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(EMAIL_SENDER, EMAIL_PASSWORD)
        s.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
    print("[OK] Email sent!")

def run_daily_leads():
    results = []
    for q in SEARCH_QUERIES:
        try:
            results.extend(search_google(q))
        except Exception as e:
            print(f"[ERROR] {e}")
    if not results:
        print("[WARN] No results")
        return
    leads = analyze_leads(results)
    today = datetime.date.today().strftime("%d/%m/%Y")
    send_email(f"GRF | לידים יומיים — {today}", leads)

if __name__ == "__main__":
    run_daily_leads()

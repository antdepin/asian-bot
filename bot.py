import requests
import time
from bs4 import BeautifulSoup

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

BLACKLIST = [
"u18",
"u19",
"u20",
"youth",
"women"
]

sent_matches = set()

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

print("BOT PARTITO")
send("🚀 Asian Scanner LIVE avviato")

def get_matches():

    url = "https://www.nowgoal.com/"
    r = requests.get(url, timeout=20)

    soup = BeautifulSoup(r.text, "html.parser")

    matches = []

    rows = soup.find_all("tr")

    for row in rows:

        text = row.get_text(" ").lower()

        if "vs" in text:

            league = text

            if any(word in league for word in BLACKLIST):
                continue

            matches.append(text)

    return matches


while True:

    try:

        print("Scanner attivo")

        matches = get_matches()

        for match in matches:

            if match not in sent_matches:

                send(f"⚽ LIVE MATCH\n\n{match}")

                sent_matches.add(match)

        time.sleep(30)

    except Exception as e:

        print("Errore:", e)

        time.sleep(30)

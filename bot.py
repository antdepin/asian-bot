import requests
import time
from bs4 import BeautifulSoup

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

sent = set()

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

send("⚽ Asian Scanner LIVE attivo")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

while True:
    try:
        r = requests.get("https://www.nowgoal.com/", headers=headers, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        rows = soup.find_all("tr")

        for row in rows:
            text = row.get_text(" ", strip=True)

            if "vs" in text.lower():
                if text not in sent:
                    send(f"⚽ LIVE MATCH\n{text}")
                    sent.add(text)

        time.sleep(30)

    except Exception as e:
        print(e)
        time.sleep(30)

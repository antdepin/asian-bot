import requests
import time
from bs4 import BeautifulSoup

TOKEN = "TUO_TOKEN"
CHAT_ID = "TUO_CHAT_ID"

URL = "https://www.nowgoal.com/football/live"

sent = set()


def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg}
    )


def get_html():
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(URL, headers=headers)
    return r.text


def parse_matches(html):
    soup = BeautifulSoup(html, "html.parser")

    matches = []

    rows = soup.select("tr")  # NowGoal usa tabelle

    for r in rows:
        try:
            text = r.get_text(" ", strip=True)

            # filtro base
            if "-" not in text:
                continue

            # esempio parsing semplice (adattabile)
            parts = text.split()

            # prova a prendere squadre
            home = parts[1]
            away = parts[3]

            score = parts[0]

            if score != "0-0":
                continue

            # minuto (NowGoal lo mette nella riga)
            minute = None
            for p in parts:
                if "'" in p:
                    minute = int(p.replace("'", ""))
                    break

            if not minute or minute < 20:
                continue

            match_id = home + away

            matches.append({
                "id": match_id,
                "home": home,
                "away": away,
                "minute": minute,
                "raw": text
            })

        except:
            continue

    return matches


send("🚀 NOWGOAL BOT ATTIVO")


while True:
    try:
        html = get_html()
        matches = parse_matches(html)

        for m in matches:

            if m["id"] in sent:
                continue

            # 🔥 QUI PUOI METTERE LE 3 REGOLE (placeholder ora)

            msg = f"""
🔥 MATCH LIVE

{m['home']} vs {m['away']}

Minuto: {m['minute']}

0-0 live → candidato
"""

            send(msg)
            sent.add(m["id"])

        time.sleep(60)

    except:
        time.sleep(60)

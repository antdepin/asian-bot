import requests
import time
from bs4 import BeautifulSoup

# ==============================
# 🔑 TELEGRAM (GIÀ INSERITI)
# ==============================

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

URL = "https://www.nowgoal.com/football/live"

sent = set()

# ==============================
# 📩 TELEGRAM
# ==============================

def send(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg}
        )
    except:
        pass

# ==============================
# 🌐 HTML
# ==============================

def get_html():
    headers = {"User-Agent": "Mozilla/5.0"}
    return requests.get(URL, headers=headers, timeout=10).text

# ==============================
# 🔢 NUMERI
# ==============================

def get_numbers(text):
    nums = []
    for t in text.split():
        try:
            nums.append(float(t))
        except:
            continue
    return nums

# ==============================
# 🔍 PARSER SERIO
# ==============================

def parse(html):

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")

    matches = []

    for r in rows:
        try:
            text = r.get_text(" ", strip=True)

            # filtro base
            if "0-0" not in text:
                continue

            if "'" not in text:
                continue

            if any(x in text.lower() for x in ["u17","u18","u19","u20","women"]):
                continue

            parts = text.split()

            # minuto
            minute = None
            for p in parts:
                if "'" in p:
                    minute = int(p.replace("'", ""))
                    break

            if not minute or minute < 20 or minute > 40:
                continue

            # squadre (più stabile)
            home = parts[1]
            away = parts[3]

            nums = get_numbers(text)

            # servono abbastanza dati
            if len(nums) < 4:
                continue

            # ultimi valori (NowGoal tipico)
            odd = nums[-1]
            tl = nums[-2]

            # filtro dati sporchi
            if tl < 1 or tl > 5:
                continue

            match_id = f"{home}-{away}"

            matches.append({
                "id": match_id,
                "home": home,
                "away": away,
                "minute": minute,
                "tl": tl,
                "odd": odd
            })

        except:
            continue

    return matches

# ==============================
# 🚀 START
# ==============================

send("🚀 BOT LIVE ASIAN AVVIATO")

while True:

    try:
        html = get_html()
        matches = parse(html)

        for m in matches:

            if m["id"] in sent:
                continue

            minute = m["minute"]
            tl = m["tl"]
            odd = m["odd"]

            # ==============================
            # 🔥 FILTRO FORTE (NO SPAM)
            # ==============================

            cond1 = tl <= 2.25          # linea bassa → match aperto
            cond2 = odd < 0.95          # quota in discesa
            cond3 = odd < 0.88          # pressione forte

            if cond1 and (cond2 or cond3):

                msg = f"""🔥 OVER 0.5 HT SETUP

{m['home']} vs {m['away']}

Minuto: {minute}

Total Line: {tl}
Quota: {odd}

✔ SETUP VALIDO"""

                send(msg)
                sent.add(m["id"])

        time.sleep(60)

    except:
        time.sleep(60)

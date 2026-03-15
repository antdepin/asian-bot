import requests
import time

print("BOT DOCKER PARTITO")

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

sent_matches = set()

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

print("BOT PARTITO")

send("⚽ Asian Scanner attivo")

def rule_r8(tl_open, tl_current, asian_open, asian_current, over_open, over_current):
    if tl_open >= 3 and tl_current >= tl_open:
        if abs(asian_open) >= 1 and abs(asian_current) >= abs(asian_open):
            if over_current < over_open:
                return True
    return False

def rule_prob(tl_open, tl_current, asian_current, over_open, over_current):
    if tl_current >= 2.75 and tl_current >= tl_open:
        if abs(asian_current) >= 1:
            return True
        if over_current < over_open:
            return True
    return False

def rule_r10(tl_open, tl_current, asian_current, over_open, over_current):
    if tl_current >= 3 and tl_current >= tl_open:
        if abs(asian_current) >= 0.75:
            return True
        if over_current < over_open:
            return True
    return False

while True:

    try:

        url = "https://api.sofascore.com/api/v1/sport/football/events/live"

        r = requests.get(url)
        data = r.json()

        events = data["events"]

        for e in events:

            home = e["homeTeam"]["name"]
            away = e["awayTeam"]["name"]

            league = e["tournament"]["name"]

            if "U18" in league or "U19" in league or "U20" in league:
                continue

            minute = e.get("time", {}).get("current", 0)

            home_score = e["homeScore"]["current"]
            away_score = e["awayScore"]["current"]

            match_id = e["id"]

            if match_id in sent_matches:
                continue

            if minute < 21:
                continue

            if home_score != 0 or away_score != 0:
                continue

            # dati odds simulati (finché non colleghiamo asianodds)
            tl_open = 3
            tl_current = 3.25
            asian_open = 1
            asian_current = 1.25
            over_open = 2.0
            over_current = 1.8

            rule1 = rule_r8(tl_open, tl_current, asian_open, asian_current, over_open, over_current)
            rule2 = rule_prob(tl_open, tl_current, asian_current, over_open, over_current)
            rule3 = rule_r10(tl_open, tl_current, asian_current, over_open, over_current)

            if rule1 or rule2 or rule3:

                msg = f"""
🔥 ASIAN SETUP TROVATO

{home} vs {away}

Minuto: {minute}
Score: 0-0

League: {league}

Regola attivata:
R8: {rule1}
Prob: {rule2}
R10: {rule3}
"""

                send(msg)

                sent_matches.add(match_id)

        time.sleep(60)

    except Exception as e:

        print("ERRORE:", e)

        time.sleep(60)

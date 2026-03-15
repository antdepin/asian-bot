import requests
import time
import os

print("BOT DOCKER PARTITO")

TOKEN = os.getenv("1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek")
CHAT_ID = os.getenv("178689360")

url = "https://api.sofascore.com/api/v1/sport/football/events/live"

def send(msg):
    telegram_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": msg
    }
    requests.post(telegram_url, data=data)

while True:
    try:

        r = requests.get(url)
        data = r.json()

        events = data["events"]

        for e in events:

            league = e["tournament"]["name"]

            if "U18" in league or "U19" in league:
                continue

            home = e["homeTeam"]["name"]
            away = e["awayTeam"]["name"]

            minute = e.get("time", {}).get("minute", 0)

            home_score = e["homeScore"]["current"]
            away_score = e["awayScore"]["current"]

            if home_score == 0 and away_score == 0 and minute >= 21:

                msg = f"""
⚽ MATCH TROVATO

{home} vs {away}

Score: {home_score}-{away_score}

League: {league}

Minute: {minute}
"""

                send(msg)

        time.sleep(60)

    except Exception as e:
        print(e)
        time.sleep(60)

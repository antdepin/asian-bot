import requests
import time

print("BOT DOCKER PARTITO")
TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

print("BOT PARTITO")
send("⚽ Asian Scanner LIVE attivo")

while True:
    try:

        url = "https://api.sofascore.com/api/v1/sport/football/events/live"
        r = requests.get(url)
        data = r.json()

        events = data["events"]

        for e in events:

            league = e["tournament"]["name"]

            if "U18" in league or "U19" in league or "U20" in league:
                continue

            home = e["homeTeam"]["name"]
            away = e["awayTeam"]["name"]

            minute = e["time"]["currentPeriodStartTimestamp"]

            home_score = e["homeScore"]["current"]
            away_score = e["awayScore"]["current"]

            if home_score == 0 and away_score == 0:

                msg = f"""
⚽ MATCH TROVATO

{home} vs {away}

Score: {home_score}-{away_score}

League: {league}
"""

                send(msg)

        time.sleep(60)

    except Exception as e:
        print(e)
        time.sleep(60)
print("docker deploy")

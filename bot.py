import requests
import math
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# ==============================
# 🔑 CONFIG
# ==============================

API_KEY = "f8a89c0e87bcd8db3ba11808f7b5aefb"
TELEGRAM_TOKEN = "8687563836:AAE8RXxf2-UWxbr7U5cFscJ8Bri6NflIS6Q"
CHAT_ID = "178689360"

headers = {"x-apisports-key": API_KEY}

team_cache = {}
form_cache = {}

# ==============================
# 📩 TELEGRAM
# ==============================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ==============================
# ⚙️ CALCOLI
# ==============================

def poisson(l,k):
    return (math.exp(-l) * l**k) / math.factorial(k)

def over25_prob(home_avg,away_avg):
    prob = 0
    for i in range(6):
        for j in range(6):
            if i + j > 2:
                prob += poisson(home_avg,i) * poisson(away_avg,j)
    return prob * 100

def team_stats(team_id,league_id,season):
    if team_id in team_cache:
        return team_cache[team_id]

    try:
        stats = requests.get(
            f"https://v3.football.api-sports.io/teams/statistics?league={league_id}&season={season}&team={team_id}",
            headers=headers
        ).json()["response"]

        played = stats["fixtures"]["played"]["total"]
        scored_home = float(stats["goals"]["for"]["average"]["home"])
        conceded_home = float(stats["goals"]["against"]["average"]["home"])
        scored_away = float(stats["goals"]["for"]["average"]["away"])
        conceded_away = float(stats["goals"]["against"]["average"]["away"])

        team_cache[team_id] = (played,scored_home,conceded_home,scored_away,conceded_away)

    except:
        team_cache[team_id] = (10,1.2,1.2,1.2,1.2)

    return team_cache[team_id]

def over_form(team_id):
    if team_id in form_cache:
        return form_cache[team_id]

    try:
        last_matches = requests.get(
            f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=10",
            headers=headers
        ).json()["response"]

        over = 0
        for m in last_matches:
            goals = m["goals"]["home"] + m["goals"]["away"]
            if goals > 2:
                over += 1

        value = (over / len(last_matches)) * 100
        form_cache[team_id] = value
        return value

    except:
        form_cache[team_id] = 50
        return 50

# ==============================
# 🚀 BOT
# ==============================

def run_bot():

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    fixtures = requests.get(
        f"https://v3.football.api-sports.io/fixtures?date={today}",
        headers=headers
    ).json()["response"]

    blocked_countries = [
    "USA","Mexico","Canada","Costa-Rica","Honduras","Panama",
    "Trinidad-And-Tobago","Jamaica","Suriname",
    "Brazil","Argentina","Chile","Colombia",
    "Peru","Uruguay","Paraguay","Venezuela",
    "South-Africa","Nigeria","Ghana","Cameroon",
    "Kenya","Tanzania",
    "Bulgaria"  # ❌ AGGIUNTO
    ]

    blocked_leagues = [
    "NPL","State League","Queensland Premier League",
    "NPL 2","Oberliga","3. liga","4. liga",
    "Division","3. SNL","Srpska Liga","Regional",
    "Tercera","Preferente","Amateur",
    "1. Liga Classic"  # ❌ AGGIUNTO
    ]

    filtered = []

    for game in fixtures:

        kickoff = datetime.fromisoformat(
            game["fixture"]["date"].replace("Z","+00:00")
        )

        if kickoff <= now:
            continue

        home = game["teams"]["home"]["name"]
        away = game["teams"]["away"]["name"]
        league = game["league"]["name"]
        country = game["league"]["country"]

        if country in blocked_countries:
            continue

        if any(x in league for x in blocked_leagues):
            continue

        if any(x in home for x in ["Women"," W","Fem"]) or any(x in away for x in ["Women"," W","Fem"]):
            continue

        if " U" in home or " U" in away:
            continue

        if "II" in home or "II" in away:
            continue

        if home.endswith(" B") or away.endswith(" B"):
            continue

        if "Reserves" in home or "Reserves" in away:
            continue

        filtered.append(game)

    candidates = []

    for game in filtered:

        home_id = game["teams"]["home"]["id"]
        away_id = game["teams"]["away"]["id"]
        league_id = game["league"]["id"]
        season = game["league"]["season"]

        home_played, home_scored_home, home_conceded_home, _, _ = team_stats(home_id,league_id,season)
        away_played, _, _, away_scored_away, away_conceded_away = team_stats(away_id,league_id,season)

        if home_played < 5 or away_played < 5:
            continue

        home_avg = (home_scored_home + away_conceded_away)/2
        away_avg = (away_scored_away + home_conceded_home)/2

        poisson_prob = over25_prob(home_avg,away_avg)

        home_form = over_form(home_id)
        away_form = over_form(away_id)

        form_prob = (home_form + away_form)/2
        final_prob = (poisson_prob * 0.6) + (form_prob * 0.4)

        if final_prob < 65:
            continue

        odds = round(100/final_prob,2)

        if odds < 1.30 or odds > 1.80:
            continue

        kickoff_local = datetime.fromisoformat(
            game["fixture"]["date"].replace("Z","+00:00")
        ).astimezone(ZoneInfo("Europe/Rome")).strftime("%H:%M")

        candidates.append({
            "match": f"{game['teams']['home']['name']} vs {game['teams']['away']['name']}",
            "prob": final_prob,
            "odds": odds,
            "time": kickoff_local,
            "league": game["league"]["name"],
            "country": game["league"]["country"],
            "home_form": home_form,
            "away_form": away_form
        })

    candidates = sorted(candidates,key=lambda x:x["prob"],reverse=True)

    message = "⚽ TOP OVER 2.5 PICKS (GIORNATA)\n\n"

    for m in candidates[:5]:

        home = m["match"].split(" vs ")[0]
        away = m["match"].split(" vs ")[1]

        message += "━━━━━━━━━━━━━━━━━━━━\n"
        message += f"⚽ {m['match']}\n\n"
        message += f"⏰ Orario: {m['time']}\n"
        message += f"🏆 Campionato: {m['league']}\n"
        message += f"🌍 Nazione: {m['country']}\n\n"
        message += f"📊 Probabilità: {round(m['prob'],1)}%\n\n"
        message += f"🔥 Forma Over:\n{home} → {round(m['home_form'],1)}%\n{away} → {round(m['away_form'],1)}%\n\n"
        message += f"💰 Quota stimata: {m['odds']}\n\n"

    send_telegram(message)

# ==============================
# ⏰ AVVIO + SCHEDULER
# ==============================

run_bot()

last_run_day = None

while True:

    now = datetime.now(ZoneInfo("Europe/Rome"))

    if now.hour == 10 and 10 <= now.minute <= 13:

        if last_run_day != now.date():

            run_bot()
            last_run_day = now.date()

    time.sleep(20)

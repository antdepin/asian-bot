import requests
import time

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

LIVE_URL = "https://api.sofascore.com/api/v1/sport/football/events/live"
EVENT_URL = "https://api.sofascore.com/api/v1/event/"

sent_matches = set()
goal_sent = set()
tracked_matches = {}

def send(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": msg
    })


def get_live_matches():

    r = requests.get(LIVE_URL)

    data = r.json()

    return data["events"]


def check_goal_first_half(match_id, home, away):

    url = f"{EVENT_URL}{match_id}"

    try:

        r = requests.get(url)

        data = r.json()

        home_score = data["event"]["homeScore"]["current"]
        away_score = data["event"]["awayScore"]["current"]

        minute = data["event"]["time"]["current"]

        if (home_score > 0 or away_score > 0) and match_id not in goal_sent:

            send(f"""✅ OVER 0.5 HT PRESO

{home} vs {away}

Minute: {minute}

Score: {home_score}-{away_score}
""")

            goal_sent.add(match_id)

    except:
        pass


def check_ht_result(match_id, home, away):

    url = f"{EVENT_URL}{match_id}"

    try:

        r = requests.get(url)

        data = r.json()

        home_ht = data["event"]["homeScore"]["period1"]
        away_ht = data["event"]["awayScore"]["period1"]

        if home_ht is not None:

            if home_ht == 0 and away_ht == 0:

                send(f"""❌ OVER 0.5 HT NON ENTRATO

{home} vs {away}

HT Score: {home_ht}-{away_ht}
""")

            else:

                send(f"""⏱ HT RESULT

{home} vs {away}

HT Score: {home_ht}-{away_ht}
""")

            return True

    except:
        pass

    return False


send("⚽ LIVE SCANNER ATTIVO")

while True:

    try:

        matches = get_live_matches()

        for m in matches:

            try:

                match_id = m["id"]

                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]

                league = m["tournament"]["name"]

                league_low = league.lower()

                if "u17" in league_low or "u19" in league_low or "women" in league_low:
                    continue

                minute = m.get("time", {}).get("current", 0)

                home_score = m["homeScore"]["current"]
                away_score = m["awayScore"]["current"]

                red_home = m.get("homeRedCards", 0)
                red_away = m.get("awayRedCards", 0)

                stats_home = m.get("homeTeamStatistics", {})
                stats_away = m.get("awayTeamStatistics", {})

                home_att = stats_home.get("dangerousAttacks", 0)
                away_att = stats_away.get("dangerousAttacks", 0)

                home_shots = stats_home.get("shotsOnGoal", 0)
                away_shots = stats_away.get("shotsOnGoal", 0)

                attacks = home_att + away_att
                shots = home_shots + away_shots

                if minute >= 21:

                    if home_score == 0 and away_score == 0:

                        if red_home == 0 and red_away == 0:

                            if attacks >= 35 and shots >= 3:

                                if match_id not in sent_matches:

                                    message = f"""
🔥 OVER 0.5 HT SETUP

{home} vs {away}

League: {league}

Minute: {minute}

Dangerous Attacks: {attacks}
Shots on Target: {shots}
"""

                                    send(message)

                                    sent_matches.add(match_id)

                                    tracked_matches[match_id] = (home, away)

                if match_id in tracked_matches:

                    if minute <= 45:

                        home_tr, away_tr = tracked_matches[match_id]

                        check_goal_first_half(match_id, home_tr, away_tr)

                    if minute >= 46:

                        home_tr, away_tr = tracked_matches[match_id]

                        if check_ht_result(match_id, home_tr, away_tr):

                            tracked_matches.pop(match_id)

            except:
                continue

        time.sleep(60)

    except:

        time.sleep(60)

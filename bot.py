import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

LIVE_URL = "https://api.sofascore.com/api/v1/sport/football/events/live"
EVENT_URL = "https://api.sofascore.com/api/v1/event/"
TZ = ZoneInfo("Europe/Rome")

sent_matches = set()
tracked_matches = {}
goal_sent = set()
resolved_matches = set()

daily_stats = {
    "analysed": 0,
    "discarded": 0,
    "setups": 0,
    "wins": 0,
    "losses": 0,
}
current_day = datetime.now(TZ).date()


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=20
        )
    except Exception:
        pass


def get_live_matches():
    try:
        r = requests.get(LIVE_URL, timeout=20)
        data = r.json()
        return data.get("events", [])
    except Exception:
        return []


def event_data(match_id):
    try:
        r = requests.get(f"{EVENT_URL}{match_id}", timeout=20)
        return r.json().get("event", {})
    except Exception:
        return {}


def send_daily_report(report_date):
    wins = daily_stats["wins"]
    losses = daily_stats["losses"]
    total_results = wins + losses
    strike = round((wins / total_results) * 100, 1) if total_results > 0 else 0.0

    msg = f"""📊 REPORT GIORNALIERO

Data: {report_date}

Partite analizzate: {daily_stats["analysed"]}
Partite scartate: {daily_stats["discarded"]}
Setup trovati: {daily_stats["setups"]}

✅ Vinte: {wins}
❌ Perse: {losses}

Percentuale successo Over HT: {strike}%
"""
    send(msg)


def reset_daily_stats():
    daily_stats["analysed"] = 0
    daily_stats["discarded"] = 0
    daily_stats["setups"] = 0
    daily_stats["wins"] = 0
    daily_stats["losses"] = 0


def maybe_rotate_daily_report():
    global current_day
    now_day = datetime.now(TZ).date()

    if now_day != current_day:
        send_daily_report(current_day)
        reset_daily_stats()
        current_day = now_day


def check_goal_first_half(match_id, home, away):
    data = event_data(match_id)
    if not data:
        return

    home_score = data.get("homeScore", {}).get("current", 0)
    away_score = data.get("awayScore", {}).get("current", 0)
    minute = data.get("time", {}).get("current", 0)

    if (home_score > 0 or away_score > 0) and match_id not in goal_sent:
        send(f"""✅ OVER 0.5 HT PRESO

{home} vs {away}

Minute: {minute}
Score: {home_score}-{away_score}
""")
        goal_sent.add(match_id)


def check_ht_result(match_id, home, away):
    if match_id in resolved_matches:
        return False

    data = event_data(match_id)
    if not data:
        return False

    home_ht = data.get("homeScore", {}).get("period1")
    away_ht = data.get("awayScore", {}).get("period1")

    if home_ht is None or away_ht is None:
        return False

    if home_ht == 0 and away_ht == 0:
        send(f"""❌ OVER 0.5 HT PERSO

{home} vs {away}

HT Score: {home_ht}-{away_ht}
""")
        daily_stats["losses"] += 1
    else:
        send(f"""⏱ HT RESULT

{home} vs {away}

HT Score: {home_ht}-{away_ht}
""")
        daily_stats["wins"] += 1

    resolved_matches.add(match_id)
    return True


send("⚽ LIVE SCANNER ATTIVO")

while True:
    try:
        maybe_rotate_daily_report()

        matches = get_live_matches()
        print("Partite live trovate:", len(matches))

        for m in matches:
            try:
                daily_stats["analysed"] += 1

                match_id = m["id"]
                home = m["homeTeam"]["name"]
                away = m["awayTeam"]["name"]
                league = m["tournament"]["name"]
                league_low = league.lower()

                if (
                    "u17" in league_low
                    or "u18" in league_low
                    or "u19" in league_low
                    or "u20" in league_low
                    or "women" in league_low
                ):
                    daily_stats["discarded"] += 1
                    print("SCARTATA categoria:", home, "vs", away)
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
                            if attacks >= 20 or shots >= 2:
                                if match_id not in sent_matches:
                                    daily_stats["setups"] += 1

                                    msg = f"""🔥 OVER 0.5 HT SETUP

{home} vs {away}

League: {league}
Minute: {minute}

Dangerous Attacks: {attacks}
Shots on Target: {shots}
"""
                                    send(msg)
                                    print("SETUP TROVATO:", home, "vs", away)

                                    sent_matches.add(match_id)
                                    tracked_matches[match_id] = (home, away)
                            else:
                                daily_stats["discarded"] += 1
                                print("SCARTATA stats:", home, "vs", away, "attacks", attacks, "shots", shots)

                if match_id in tracked_matches:
                    home_tr, away_tr = tracked_matches[match_id]

                    if minute <= 45:
                        check_goal_first_half(match_id, home_tr, away_tr)

                    if minute >= 46:
                        if check_ht_result(match_id, home_tr, away_tr):
                            tracked_matches.pop(match_id, None)

            except Exception:
                continue

        wins = daily_stats["wins"]
        losses = daily_stats["losses"]
        total_results = wins + losses
        strike = round((wins / total_results) * 100, 1) if total_results > 0 else 0.0

        print("----- REPORT -----")
        print("Analizzate:", daily_stats["analysed"])
        print("Scartate:", daily_stats["discarded"])
        print("Setup trovati:", daily_stats["setups"])
        print("Vinte:", wins)
        print("Perse:", losses)
        print("Successo Over HT:", f"{strike}%")
        print("------------------")

        time.sleep(60)

    except Exception:
        time.sleep(60)

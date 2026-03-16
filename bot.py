import requests
import time
import re
import unicodedata
from playwright.sync_api import sync_playwright

print("BOT DOCKER PARTITO")

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

SOFASCORE_URL = "https://api.sofascore.com/api/v1/sport/football/events/live"
ASIANODDS_URL = "https://www.asianodds.com/en/football/live"

sent_matches = set()


def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=20)


def normalize(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def short_name(name):
    name = normalize(name)
    words = name.split()
    if len(words) >= 2:
        return words[0][:4] + words[1][:4]
    else:
        return words[0][:6]


def team_key(home, away):
    return short_name(home) + "-" + short_name(away)


def get_live_matches():

    r = requests.get(SOFASCORE_URL)
    data = r.json()

    events = data["events"]
    matches = []

    for e in events:

        try:

            league = e["tournament"]["name"]

            if "u17" in normalize(league) or "u19" in normalize(league) or "women" in normalize(league):
                continue

            home = e["homeTeam"]["name"]
            away = e["awayTeam"]["name"]

            minute = int(e.get("time", {}).get("current", 0))

            home_score = e["homeScore"]["current"]
            away_score = e["awayScore"]["current"]

            red_home = int(e.get("homeRedCards", 0))
            red_away = int(e.get("awayRedCards", 0))

            if minute < 21:
                continue

            if home_score != 0 or away_score != 0:
                continue

            if red_home != 0 or red_away != 0:
                continue

            matches.append({
                "home": home,
                "away": away,
                "minute": minute,
                "league": league,
                "key": team_key(home, away)
            })

        except:
            continue

    return matches


def parse_numbers(text):
    nums = re.findall(r"-?\d+\.?\d*", text)
    return [float(x) for x in nums]


def get_asianodds():

    rows = []

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(ASIANODDS_URL)

        page.wait_for_timeout(8000)

        body = page.locator("body").inner_text()

        browser.close()

    lines = body.split("\n")

    for i, line in enumerate(lines):

        if " vs " not in line.lower():
            continue

        try:

            home, away = line.split(" vs ")

            nums = parse_numbers(" ".join(lines[i:i+6]))

            if len(nums) < 6:
                continue

            rows.append({

                "key": team_key(home, away),

                "asian_open": nums[0],
                "asian_current": nums[1],

                "tl_open": nums[2],
                "tl_current": nums[3],

                "over_open": nums[4],
                "over_current": nums[5]

            })

        except:
            continue

    return rows


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


def rule_r10(tl_open, tl_current, asian_open, asian_current, over_open, over_current):

    if tl_current >= 3 and tl_current >= tl_open:

        if abs(asian_current) >= 0.75 and abs(asian_open) >= 1:
            return True

        if over_current < over_open:
            return True

    return False


print("BOT PARTITO")

send("⚽ Asian Scanner attivo")


while True:

    try:

        live_matches = get_live_matches()
        asian_rows = get_asianodds()

        asian_map = {r["key"]: r for r in asian_rows}

        for match in live_matches:

            key = match["key"]

            if key not in asian_map:
                continue

            if key in sent_matches:
                continue

            odds = asian_map[key]

            r8 = rule_r8(
                odds["tl_open"],
                odds["tl_current"],
                odds["asian_open"],
                odds["asian_current"],
                odds["over_open"],
                odds["over_current"]
            )

            prob = rule_prob(
                odds["tl_open"],
                odds["tl_current"],
                odds["asian_current"],
                odds["over_open"],
                odds["over_current"]
            )

            r10 = rule_r10(
                odds["tl_open"],
                odds["tl_current"],
                odds["asian_open"],
                odds["asian_current"],
                odds["over_open"],
                odds["over_current"]
            )

            if r8 or prob or r10:

                regola = "R8" if r8 else "PROB" if prob else "R10"

                msg = f"""
🔥 ASIAN SETUP

{match["home"]} vs {match["away"]}

Minute: {match["minute"]}
League: {match["league"]}

TL open: {odds["tl_open"]}
TL current: {odds["tl_current"]}

Asian open: {odds["asian_open"]}
Asian current: {odds["asian_current"]}

Over open: {odds["over_open"]}
Over current: {odds["over_current"]}

Regola: {regola}
"""

                send(msg)

                sent_matches.add(key)

        time.sleep(60)

    except Exception as e:

        print("ERRORE:", e)

        time.sleep(60)

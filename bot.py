import requests
import time
import re
import unicodedata
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

print("BOT DOCKER PARTITO")

# LASCIA QUI IL TUO TOKEN
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
    text = text.lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def team_key(home, away):
    return f"{normalize(home)} vs {normalize(away)}"


def safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def parse_float(txt):
    try:
        return float(str(txt).replace(",", "").strip())
    except Exception:
        return None


def get_live_matches():
    r = requests.get(SOFASCORE_URL, timeout=20)
    data = r.json()
    events = data.get("events", [])

    matches = []

    for e in events:
        try:
            league = e["tournament"]["name"]

            # esclusioni base
            bad_words = ["u17", "u18", "u19", "u20", "women", "youth", "friendly"]
            if any(x in normalize(league) for x in bad_words):
                continue

            home = e["homeTeam"]["name"]
            away = e["awayTeam"]["name"]

            minute = safe_int(e.get("time", {}).get("current", 0), 0)

            home_score = safe_int(e.get("homeScore", {}).get("current", 0), 0)
            away_score = safe_int(e.get("awayScore", {}).get("current", 0), 0)

            red_home = safe_int(e.get("homeRedCards", 0), 0)
            red_away = safe_int(e.get("awayRedCards", 0), 0)

            match_id = str(e["id"])

            # filtro base richiesto
            if minute < 21:
                continue
            if not (home_score == 0 and away_score == 0):
                continue
            if red_home != 0 or red_away != 0:
                continue

            matches.append({
                "id": match_id,
                "home": home,
                "away": away,
                "league": league,
                "minute": minute,
                "score": f"{home_score}-{away_score}",
                "key": team_key(home, away)
            })
        except Exception:
            continue

    return matches


def extract_numbers(line):
    nums = re.findall(r"[-+]?\d+(?:\.\d+)?", line)
    return [parse_float(x) for x in nums if parse_float(x) is not None]


def parse_asianodds_table(page_text):
    """
    Parser semplice basato sul testo della tabella.
    Restituisce una lista di record con:
    home, away, asian_open, asian_current, tl_open, tl_current, over_open, over_current
    """
    rows = []
    lines = [x.strip() for x in page_text.splitlines() if x.strip()]

    # Prova a trovare righe che contengono 'vs'
    for i, line in enumerate(lines):
        low = normalize(line)
        if " vs " not in low:
            continue

        match_line = line
        nums_block = " ".join(lines[i:i + 8])  # prende alcune righe dopo il match
        nums = extract_numbers(nums_block)

        # Qui facciamo una lettura "best effort"
        # AsianOdds può cambiare layout, quindi usiamo posizioni indicative.
        # Se i dati non si capiscono, il record viene saltato.
        if len(nums) < 6:
            continue

        try:
            home, away = [x.strip() for x in re.split(r"\bvs\b", match_line, flags=re.I, maxsplit=1)]

            # mappatura semplice:
            # asian_open, asian_current, tl_open, tl_current, over_open, over_current
            asian_open = nums[0]
            asian_current = nums[1]
            tl_open = nums[2]
            tl_current = nums[3]
            over_open = nums[4]
            over_current = nums[5]

            rows.append({
                "home": home,
                "away": away,
                "key": team_key(home, away),
                "asian_open": asian_open,
                "asian_current": asian_current,
                "tl_open": tl_open,
                "tl_current": tl_current,
                "over_open": over_open,
                "over_current": over_current
            })
        except Exception:
            continue

    return rows


def get_asianodds_rows():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(ASIANODDS_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(8000)

        # scroll piccolo per caricare eventuali righe live
        page.mouse.wheel(0, 1200)
        page.wait_for_timeout(3000)

        text = page.locator("body").inner_text()
        browser.close()

    return parse_asianodds_table(text)


def rule_r8(tl_open, tl_current, asian_open, asian_current, over_open, over_current):
    if tl_open is None or tl_current is None or asian_open is None or asian_current is None or over_open is None or over_current is None:
        return False
    if tl_open >= 3 and tl_current >= tl_open:
        if abs(asian_open) >= 1 and abs(asian_current) >= abs(asian_open):
            if over_current < over_open:
                return True
    return False


def rule_prob(tl_open, tl_current, asian_current, over_open, over_current):
    if tl_open is None or tl_current is None or asian_current is None or over_open is None or over_current is None:
        return False
    if tl_current >= 2.75 and tl_current >= tl_open:
        if abs(asian_current) >= 1:
            return True
        if over_current < over_open:
            return True
    return False


def rule_r10(tl_open, tl_current, asian_open, asian_current, over_open, over_current):
    if tl_open is None or tl_current is None or asian_open is None or asian_current is None or over_open is None or over_current is None:
        return False
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
        asian_rows = get_asianodds_rows()

        asian_map = {r["key"]: r for r in asian_rows}

        for match in live_matches:
            if match["id"] in sent_matches:
                continue

            odds = asian_map.get(match["key"])
            if not odds:
                continue

            r8 = rule_r8(
                odds["tl_open"], odds["tl_current"],
                odds["asian_open"], odds["asian_current"],
                odds["over_open"], odds["over_current"]
            )

            prob = rule_prob(
                odds["tl_open"], odds["tl_current"],
                odds["asian_current"],
                odds["over_open"], odds["over_current"]
            )

            r10 = rule_r10(
                odds["tl_open"], odds["tl_current"],
                odds["asian_open"], odds["asian_current"],
                odds["over_open"], odds["over_current"]
            )

            if r8 or prob or r10:
                active_rule = "R8" if r8 else "PROB" if prob else "R10"

                msg = f"""🔥 ASIAN SETUP

{match["home"]} vs {match["away"]}

Minute: {match["minute"]}
Score: {match["score"]}
League: {match["league"]}

TL open: {odds["tl_open"]}
TL current: {odds["tl_current"]}

Asian open: {odds["asian_open"]}
Asian current: {odds["asian_current"]}

Over open: {odds["over_open"]}
Over current: {odds["over_current"]}

Regola: {active_rule}
"""

                send(msg)
                sent_matches.add(match["id"])

        time.sleep(60)

    except Exception as e:
        print("ERRORE:", e)
        time.sleep(60)

import requests
import time
import re
import unicodedata
from difflib import SequenceMatcher
from playwright.sync_api import sync_playwright

print("BOT DOCKER PARTITO")

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

SOFASCORE_URL = "https://api.sofascore.com/api/v1/sport/football/events/live"
ASIANODDS_URL = "https://www.asianodds.com/en/football/live"

sent_matches = set()

BAD_LEAGUES = [
"u17","u18","u19","u20","u21",
"women","ladies","friendly",
"youth","reserve"
]

TEAM_ALIASES = {
"utd":"united",
"man utd":"manchester united",
"man united":"manchester united",
"psg":"paris saint germain",
"fc":"",
"sc":"",
"ac":"",
"cd":""
}

def send(msg):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url,data={"chat_id":CHAT_ID,"text":msg},timeout=20)
    except:
        pass


def normalize(text):

    text = unicodedata.normalize("NFKD",text).encode("ascii","ignore").decode("ascii")
    text = text.lower()

    for old,new in TEAM_ALIASES.items():
        text = text.replace(old,new)

    text = re.sub(r"[^a-z0-9\s]"," ",text)
    text = re.sub(r"\s+"," ",text)

    return text.strip()


def similarity(a,b):

    return SequenceMatcher(None,a,b).ratio()


def get_live_matches():

    matches=[]

    r=requests.get(SOFASCORE_URL)
    data=r.json()

    for e in data["events"]:

        try:

            league=e["tournament"]["name"]

            if any(x in normalize(league) for x in BAD_LEAGUES):
                continue

            home=e["homeTeam"]["name"]
            away=e["awayTeam"]["name"]

            minute=int(e.get("time",{}).get("current",0))

            hs=e["homeScore"]["current"]
            ascore=e["awayScore"]["current"]

            red_home=int(e.get("homeRedCards",0))
            red_away=int(e.get("awayRedCards",0))

            if minute < 21:
                continue

            if hs!=0 or ascore!=0:
                continue

            if red_home!=0 or red_away!=0:
                continue

            matches.append({

                "id":e["id"],
                "home":home,
                "away":away,
                "league":league,
                "minute":minute,
                "home_n":normalize(home),
                "away_n":normalize(away)

            })

        except:
            continue

    return matches


def extract_numbers(text):

    nums=re.findall(r"-?\d+\.?\d*",text)

    return [float(x) for x in nums]


def get_asian():

    rows=[]

    with sync_playwright() as p:

        browser=p.chromium.launch(headless=True)

        page=browser.new_page()

        page.goto(ASIANODDS_URL)

        page.wait_for_timeout(8000)

        body=page.locator("body").inner_text()

        browser.close()

    lines=body.split("\n")

    for i,line in enumerate(lines):

        if " vs " not in line.lower():
            continue

        try:

            home,away=line.split(" vs ")

            nums=extract_numbers(" ".join(lines[i:i+10]))

            if len(nums) < 6:
                continue

            rows.append({

            "home":home,
            "away":away,

            "home_n":normalize(home),
            "away_n":normalize(away),

            "asian_open":nums[0],
            "asian_current":nums[1],

            "tl_open":nums[2],
            "tl_current":nums[3],

            "over_open":nums[4],
            "over_current":nums[5]

            })

        except:
            continue

    return rows


def match_row(match,rows):

    best=None
    best_score=0

    for r in rows:

        s1=similarity(match["home_n"],r["home_n"])
        s2=similarity(match["away_n"],r["away_n"])

        score=(s1+s2)/2

        if score>best_score:

            best_score=score
            best=r

    if best_score>0.7:
        return best

    return None


def rule_r8(tl_open,tl_current,asian_open,asian_current,over_open,over_current):

    if tl_open>=3 and tl_current>=tl_open:

        if abs(asian_open)>=1 and abs(asian_current)>=abs(asian_open):

            if over_current<over_open:

                return True

    return False


def rule_prob(tl_open,tl_current,asian_current,over_open,over_current):

    if tl_current>=2.75 and tl_current>=tl_open:

        if abs(asian_current)>=1:
            return True

        if over_current<over_open:
            return True

    return False


def rule_r10(tl_open,tl_current,asian_open,asian_current,over_open,over_current):

    if tl_current>=3 and tl_current>=tl_open:

        if abs(asian_current)>=0.75 and abs(asian_open)>=1:
            return True

        if over_current<over_open:
            return True

    return False


print("BOT PARTITO")

send("⚽ Asian Scanner attivo")


while True:

    try:

        live=get_live_matches()

        asian=get_asian()

        for match in live:

            if match["id"] in sent_matches:
                continue

            odds=match_row(match,asian)

            if not odds:
                continue

            r8=rule_r8(
            odds["tl_open"],
            odds["tl_current"],
            odds["asian_open"],
            odds["asian_current"],
            odds["over_open"],
            odds["over_current"]
            )

            prob=rule_prob(
            odds["tl_open"],
            odds["tl_current"],
            odds["asian_current"],
            odds["over_open"],
            odds["over_current"]
            )

            r10=rule_r10(
            odds["tl_open"],
            odds["tl_current"],
            odds["asian_open"],
            odds["asian_current"],
            odds["over_open"],
            odds["over_current"]
            )

            if r8 or prob or r10:

                rule="R8" if r8 else "PROB" if prob else "R10"

                msg=f"""
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

Rule: {rule}
"""

                send(msg)

                sent_matches.add(match["id"])

        time.sleep(60)

    except Exception as e:

        print("ERROR",e)

        time.sleep(60)

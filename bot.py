import requests
import time
from datetime import datetime
from zoneinfo import ZoneInfo

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

LIVE_URL = "https://api.sofascore.com/api/v1/sport/football/events/live"
EVENT_URL = "https://api.sofascore.com/api/v1/event/"
STATS_URL = "https://api.sofascore.com/api/v1/event/{}/statistics"

TZ = ZoneInfo("Europe/Rome")

sent_matches=set()
tracked_matches=set()
resolved=set()

daily={
"analysed":0,
"discarded":0,
"setups":0,
"wins":0,
"losses":0
}

current_day=datetime.now(TZ).date()


def send(msg):

    url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    try:
        requests.post(url,data={"chat_id":CHAT_ID,"text":msg},timeout=20)
    except:
        pass


def get_live():

    try:
        r=requests.get(LIVE_URL,timeout=20)
        return r.json()["events"]
    except:
        return []


def get_event(id):

    try:
        r=requests.get(EVENT_URL+str(id),timeout=20)
        return r.json()["event"]
    except:
        return {}


def get_stats(id):

    try:

        r=requests.get(STATS_URL.format(id),timeout=20)

        data=r.json()

        attacks=0
        shots=0
        corners=0

        for g in data.get("statistics",[]):

            for group in g.get("groups",[]):

                for s in group.get("statisticsItems",[]):

                    name=s.get("name","").lower()

                    if "dangerous attacks" in name:

                        attacks=int(s["home"])+int(s["away"])

                    if "shots on target" in name:

                        shots=int(s["home"])+int(s["away"])

                    if "corner" in name:

                        corners=int(s["home"])+int(s["away"])

        return attacks,shots,corners

    except:

        return 0,0,0


def report():

    wins=daily["wins"]
    losses=daily["losses"]

    total=wins+losses

    strike=round((wins/total)*100,1) if total>0 else 0

    send(f"""
📊 REPORT GIORNALIERO

Analizzate {daily["analysed"]}
Scartate {daily["discarded"]}
Setup {daily["setups"]}

✅ Vinte {wins}
❌ Perse {losses}

Successo {strike}%
""")


def rotate_day():

    global current_day

    today=datetime.now(TZ).date()

    if today!=current_day:

        report()

        for k in daily:
            daily[k]=0

        current_day=today


def goal_check(id,home,away):

    data=get_event(id)

    if not data:
        return

    hs=data["homeScore"]["current"]
    as_=data["awayScore"]["current"]

    minute=data.get("time",{}).get("current",0)

    if hs>0 or as_>0:

        send(f"""
✅ OVER 0.5 HT PRESO

{home} vs {away}

Minute {minute}

Score {hs}-{as_}
""")


def ht_check(id,home,away):

    if id in resolved:
        return False

    data=get_event(id)

    if not data:
        return False

    h=data["homeScore"].get("period1")
    a=data["awayScore"].get("period1")

    if h is None:
        return False

    if h==0 and a==0:

        send(f"""
❌ OVER 0.5 HT PERSO

{home} vs {away}

HT {h}-{a}
""")

        daily["losses"]+=1

    else:

        send(f"""
⏱ HT RESULT

{home} vs {away}

HT {h}-{a}
""")

        daily["wins"]+=1

    resolved.add(id)

    return True


send("⚽ SCANNER LIVE ATTIVO")


while True:

    try:

        rotate_day()

        matches=get_live()

        print("Live trovate:",len(matches))

        for m in matches:

            try:

                daily["analysed"]+=1

                id=m["id"]

                home=m["homeTeam"]["name"]
                away=m["awayTeam"]["name"]

                league=m["tournament"]["name"].lower()

                if "u17" in league or "u19" in league or "women" in league:

                    daily["discarded"]+=1
                    continue

                minute=m.get("time",{}).get("current",0)

                hs=m["homeScore"]["current"]
                aw=m["awayScore"]["current"]

                # nuova finestra minuti
                if minute<18 or minute>45:
                    continue

                if hs>0 or aw>0:
                    continue

                attacks,shots,corners=get_stats(id)

                # filtro migliorato
                if attacks>=18 or shots>=2 or corners>=3:

                    if id not in sent_matches:

                        daily["setups"]+=1

                        send(f"""
🔥 OVER 0.5 HT SETUP

{home} vs {away}

Minute {minute}

Attacks {attacks}
Shots {shots}
Corners {corners}
""")

                        sent_matches.add(id)

                        tracked_matches.add(id)

                # goal imminente
                if attacks>=40 and shots>=4:

                    send(f"""
⚡ GOAL IMMINENTE

{home} vs {away}

Minute {minute}

Attacks {attacks}
Shots {shots}
Corners {corners}
""")

                if id in tracked_matches:

                    if minute<=45:

                        goal_check(id,home,away)

                    if minute>=46:

                        if ht_check(id,home,away):

                            tracked_matches.remove(id)

            except:
                continue

        wins=daily["wins"]
        losses=daily["losses"]

        total=wins+losses

        strike=round((wins/total)*100,1) if total>0 else 0

        print("----- REPORT -----")
        print("Analizzate",daily["analysed"])
        print("Scartate",daily["discarded"])
        print("Setup",daily["setups"])
        print("Vinte",wins)
        print("Perse",losses)
        print("Successo",strike,"%")
        print("------------------")

        time.sleep(60)

    except:

        time.sleep(60)

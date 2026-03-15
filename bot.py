import requests
import time

TOKEN="8687563836:AAE8RXxf2-UWxbr7U5cFscJ8Bri6NflIS6Q"
CHAT_ID="178689360"

def send(msg):
    url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url,data={"chat_id":CHAT_ID,"text":msg})

while True:

    try:

        r=requests.get("https://www.nowgoal.com/football/live")

        if "football" in r.text:

            print("scanner live")

        time.sleep(30)

    except:

        time.sleep(30)

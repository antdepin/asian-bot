import requests
import time

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

print("BOT PARTITO")
send("BOT PARTITO")

while True:
    try:
        print("scanner attivo")
        send("scanner attivo")
        time.sleep(30)
    except Exception as e:
        print(e)
        time.sleep(30)

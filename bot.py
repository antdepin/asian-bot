
import requests
import time

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=20)

print("BOT LIVE AVVIATO")

while True:
    try:
        # controllo sito live
        r = requests.get("https://www.nowgoal.com/", timeout=20)
        text = r.text.lower()

        if "football" in text:
            send("⚡ Scanner live attivo")

        time.sleep(30)

    except Exception as e:
        print("Errore:", e)
        time.sleep(30)

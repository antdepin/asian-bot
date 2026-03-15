import asyncio
from playwright.async_api import async_playwright
import requests

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

sent=set()

def send(msg):
    url=f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url,data={"chat_id":CHAT_ID,"text":msg})


async def scan():

    async with async_playwright() as p:

        browser=await p.chromium.launch(headless=True)
        page=await browser.new_page()

        await page.goto("https://www.nowgoal.com/")

        while True:

            rows=await page.query_selector_all("tr")

            for row in rows:

                text=await row.inner_text()

                if "vs" in text.lower():

                    if text not in sent:

                        send(f"⚽ LIVE MATCH\n\n{text}")
                        sent.add(text)

            await asyncio.sleep(30)


print("BOT PARTITO")
send("⚽ Asian Scanner LIVE attivo")

asyncio.run(scan())

import asyncio
import requests
from playwright.async_api import async_playwright

TOKEN = "1292804066:AAHIGsAOWz3vBXF4RJBnnQGH9m2UgNfJhek"
CHAT_ID = "178689360"

def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

async def scan():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto("https://www.asianodds.com/en", timeout=60000)

        text = await page.content()

        if "OU Points" in text:
            send("🔥 AsianOdds scanner attivo")

        await browser.close()

async def main():
    while True:
        try:
            await scan()
        except Exception as e:
            print(e)

        await asyncio.sleep(30)

asyncio.run(main())

import asyncio
import os
import time
from datetime import datetime
from telegram import Bot
from playwright.async_api import async_playwright

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=BOT_TOKEN)

previous_data = []

async def get_positions():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="en-US",
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )
        page = await context.new_page()

        url = "https://www.binance.com/en/copy-trading/lead-details/4466349480575764737?timeRange=30D"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(15000)  # 給 JS 載入時間

        rows = await page.query_selector_all("tr.bn-web-table-row")
        output = []

        for row in rows:
            cells = await row.query_selector_all("td")
            if len(cells) >= 2:
                symbol = (await cells[0].inner_text()).strip()
                size_raw = (await cells[1].inner_text()).strip()
                parts = size_raw.split()
                if len(parts) == 2:
                    qty_str, asset = parts
                    direction = "Short" if "-" in qty_str else "Long"
                    qty = qty_str.replace("-", "")
                    output.append(f"{symbol} | {direction} | {qty} {asset}")

        await browser.close()
        return output

async def notify_if_changed():
    global previous_data
    print(f"[{datetime.now()}] 🕵️ 正在檢查 Positions...")
    data = await get_positions()
    if data != previous_data:
        message = "📈【Binance Position 更新】\n" + "\n".join(data)
        print(f"[{datetime.now()}] ✅ 有變化，發送通知")
        await bot.send_message(chat_id=CHAT_ID, text=message)
        previous_data = data
    else:
        print(f"[{datetime.now()}] 🔁 無變化")

async def loop_forever():
    while True:
        try:
            await notify_if_changed()
        except Exception as e:
            print(f"[{datetime.now()}] ❌ 錯誤: {e}")
        time.sleep(300)  # 每 5 分鐘檢查一次

if __name__ == "__main__":
    asyncio.run(loop_forever())

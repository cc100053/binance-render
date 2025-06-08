import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from telegram import Bot
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=BOT_TOKEN)

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
        print(f"[{datetime.now()}] 🌐 連線中...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        await page.wait_for_timeout(15000)  # 等 JS 資料載入
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

async def main():
    print(f"[{datetime.now()}] ▶️ Binance 監控啟動")
    data = await get_positions()
    if data:
        msg = "📈【Binance Position 更新】\n" + "\n".join(data)
        await bot.send_message(chat_id=CHAT_ID, text=msg)
    else:
        print(f"[{datetime.now()}] ℹ️ 無資料")

asyncio.run(main())

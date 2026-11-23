import os, requests, datetime, asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
MY_ID = int(os.environ.get("CHAT_ID", "7469070"))
daily_count = 0
last_date = datetime.date.today()
last_signal_time = None

def get_usdjpy():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/USDJPY=X?range=5d&interval=15m"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15).json()
    closes = r["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    closes = [c for c in closes if c is not None]
    return closes

def rsi(closes, period=14):
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i]-closes[i-1]
        gains.append(max(d,0)); losses.append(max(-d,0))
    avg_g = sum(gains[-period:])/period
    avg_l = sum(losses[-period:])/period
    if avg_l == 0: return 100
    return 100 - (100/(1+avg_g/avg_l))

def ema(closes, period):
    k = 2/(period+1); e = closes[0]
    for c in closes[1:]: e = c*k + e*(1-k)
    return e

def check():
    closes = get_usdjpy()
    price = closes[-1]; r = rsi(closes); e20 = ema(closes, 20); e50 = ema(closes, 50)
    if r < 32 and price > e20 > e50:
        return "🟢 BUY / LONG", price, r, price-0.30, price+0.50
    if r > 68 and price < e20 < e50:
        return "🔴 SELL / SHORT", price, r, price+0.30, price-0.50
    return None, price, r, 0, 0

async def auto_check(context: ContextTypes.DEFAULT_TYPE):
    global daily_count, last_date, last_signal_time
    today = datetime.date.today()
    if today != last_date:
        daily_count = 0; last_date = today; last_signal_time = None
    if daily_count >= 10: return
    if last_signal_time and (datetime.datetime.now() - last_signal_time).total_seconds() < 3600: return
    try:
        sig, price, r, sl, tp = check()
        if sig:
            daily_count += 1
            last_signal_time = datetime.datetime.now()
            msg = f"🚀 {daily_count}/10 - USD/JPY SIGNAL\n\n{sig}\nPrice: {price:.2f}\nRSI: {r:.1f}\nSL: {sl:.2f}\nTP: {tp:.2f}"
            await context.bot.send_message(chat_id=MY_ID, text=msg)
    except Exception as e:
        print(f"Error: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"✅ USD/JPY Bot Running!\nUse /signal for live signal\nUse /status for status")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sig, price, r, sl, tp = check()
        await update.message.reply_text(f"📊 USD/JPY Status\nPrice: {price:.2f}\nRSI: {r:.1f}\nToday Signals: {daily_count}/10")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ USD/JPY Checking...")
    await auto_check(context)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("status", status))
    app.job_queue.run_repeating(auto_check, interval=300, first=10)
    print("USDJPY Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()

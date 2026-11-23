import os, requests, datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
TOKEN = os.environ.get("BOT_TOKEN")
MY_ID = int(os.environ.get("CHAT_ID", "7469070313"))
daily_count = 0
last_date = datetime.date.today()
last_signal_time = None
def get_usdjpy():
    url = "https://query1.finance.yahoo.com/v8/finance/chart/USDJPY=X?interval=15m&range=2d"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=10).json()
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
        return "🟢 BUY / LONG", price, r, price-0.25, price+0.45
    if r > 68 and price < e20 < e50:
        return "🔴 SELL / SHORT", price, r, price+0.25, price-0.45
    return None, price, r, 0, 0
async def auto_check(context):
    global daily_count, last_date, last_signal_time
    today = datetime.date.today()
    if today != last_date:
        daily_count = 0; last_date = today; last_signal_time = None
    if daily_count >= 10: return
    if last_signal_time and (datetime.datetime.now() - last_signal_time).seconds < 3600:
        return
    try:
        sig, price, r, sl, tp = check()
        if sig:
            daily_count += 1
            last_signal_time = datetime.datetime.now()
            msg = f"🚀 {daily_count}/10 - USD/JPY SIGNAL\n\nPair: USD/JPY\nSignal: {sig}\nPrice: {price:.3f}\nRSI: {r:.1f}\n\n🎯 TP: {tp:.3f}\n🛑 SL: {sl:.3f}\n⏰ Timeframe: 15m\n\n⚠️ 1-2% এর বেশি রিস্ক নিও না।"
            await context.bot.send_message(chat_id=MY_ID, text=msg)
    except: pass
async def start(update, context):
    await update.message.reply_text(f"✅ USD/JPY Bot 24h চালু!\n\nআজকে: {daily_count}/10 টা\n\n/signal - এখন চেক করো\n/status - কয়টা বাকি")
async def status(update, context):
    await update.message.reply_text(f"📊 USD/JPY\nআজকে: {daily_count}/10 টা\nবাকি: {10-daily_count} টা\n\nফোন অফ থাকলেও চলবো।")
async def signal(update, context):
    await update.message.reply_text("⏳ USD/JPY ভালো সিগন্যাল খুঁজতেছি...")
    await auto_check(context)
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("status", status))
app.job_queue.run_repeating(auto_check, interval=900, first=10)
print("USDJPY Bot Running...")
app.run_polling()

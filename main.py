import logging
import requests
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# === ✅ Your Telegram Bot Token ===
BOT_TOKEN = "7875515823:AAHTTzPVTWPZLi8RE4xURGE5dnmUh1eoaT0"

# === ✅ Google Sheets Setup ===
SHEET_NAME = "Trade Journal"


# Google Sheets Auth
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["CREDS_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# === Logging Config ===
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# === Fetch Price Function (from Yahoo Finance) ===
def fetch_price(symbol):
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    response = requests.get(url).json()
    result = response['quoteResponse']['result']
    if not result:
        return None
    data = result[0]
    return {
        "name": data.get("longName", symbol),
        "price": data.get("regularMarketPrice", 0),
        "change": data.get("regularMarketChangePercent", 0),
        "currency": data.get("currency", "INR")
    }

# === Log Signal to Google Sheet ===
def log_to_sheet(symbol, price, signal):
    row = [time.strftime("%Y-%m-%d %H:%M:%S"), symbol, price, signal]
    sheet.append_row(row)

# === Bot Command: /start ===
def start(update: Update, context: CallbackContext):
    update.message.reply_text("🤖 Welcome to Tokir's Trading Bot!\nUse /analyze SYMBOL\nExample: /analyze RELIANCE")

# === Bot Command: /analyze SYMBOL ===
def analyze(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("⚠️ Please use: /analyze SYMBOL")
        return
    symbol = context.args[0].upper()
    data = fetch_price(symbol)
    if not data:
        update.message.reply_text(f"❌ No data found for '{symbol}'")
        return
    price = data["price"]
    signal = "BUY ✅" if data["change"] > 0 else "SELL ❌"
    log_to_sheet(symbol, price, signal)
    update.message.reply_text(
        f"📊 {data['name']} ({symbol})\n💰 Price: {price} {data['currency']}\n📈 Signal: {signal}"
    )

# === Bot Launcher ===
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("analyze", analyze))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

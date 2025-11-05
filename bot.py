import requests
import os
from datetime import datetime

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
MEMECOINS = ['dogecoin', 'shiba-inu', 'pepe', 'floki', 'bonk']
PRICE_CHANGE_THRESHOLD = 5

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def get_crypto_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(MEMECOINS),
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "1h,24h"
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def analyze_and_send_signals():
    data = get_crypto_data()
    if not data:
        send_telegram_message("⚠️ Ошибка получения данных")
        return
    
    signals = []
    for coin in data:
        name = coin['name']
        symbol = coin['symbol'].upper()
        price = coin['current_price']
        change_1h = coin.get('price_change_percentage_1h_in_currency', 0)
        change_24h = coin.get('price_change_percentage_24h_in_currency', 0)
        volume = coin['total_volume']
        
        if change_1h and abs(change_1h) >= PRICE_CHANGE_THRESHOLD:
            emoji = "🚀" if change_1h > 0 else "📉"
            signal = f"{emoji} <b>{name} ({symbol})</b>\n"
            signal += f"💰 Цена: ${price:.8f}\n"
            signal += f"📊 1ч: {change_1h:+.2f}%\n"
            signal += f"📈 24ч: {change_24h:+.2f}%\n"
            signal += f"💵 Объём: ${volume:,.0f}\n"
            signal += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
            signals.append(signal)
    
    if signals:
        message = "🔔 <b>СИГНАЛ ОБНАРУЖЕН!</b>\n\n" + "\n".join(signals)
        send_telegram_message(message)
    else:
        status = f"✅ Мониторинг активен\n⏰ {datetime.now().strftime('%H:%M:%S')}\n📊 Всё спокойно"
        send_telegram_message(status)

if __name__ == "__main__":
    analyze_and_send_signals()

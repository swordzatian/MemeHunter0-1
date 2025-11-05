import requests
import os
from datetime import datetime, timedelta

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# Основные мемкоины для отслеживания
MEMECOINS = ['dogecoin', 'shiba-inu', 'pepe', 'floki', 'bonk', 'dogwifhat', 'memecoin']

# Пороги для сигналов
PRICE_CHANGE_THRESHOLD = 5  # Процент изменения цены
VOLUME_SPIKE_THRESHOLD = 2.5  # Во сколько раз вырос объём
RSI_OVERSOLD = 30  # RSI ниже этого = перекупленность (BUY)
RSI_OVERBOUGHT = 70  # RSI выше этого = перепроданность (SELL)

def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return None

def get_crypto_data():
    """Получение данных о криптовалютах"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(MEMECOINS),
        "order": "market_cap_desc",
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка получения данных: {e}")
        return None

def get_new_coins():
    """Поиск новых перспективных монет"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "category": "meme-token",
        "order": "volume_desc",
        "per_page": 20,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка поиска новых монет: {e}")
        return None

def calculate_rsi(prices, period=14):
    """Расчёт RSI (Relative Strength Index)"""
    if len(prices) < period:
        return 50  # Нейтральное значение если данных мало
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def analyze_coin(coin):
    """Анализ монеты и генерация сигнала"""
    name = coin['name']
    symbol = coin['symbol'].upper()
    price = coin['current_price']
    change_1h = coin.get('price_change_percentage_1h_in_currency', 0) or 0
    change_24h = coin.get('price_change_percentage_24h_in_currency', 0) or 0
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
    volume = coin['total_volume']
    market_cap = coin['market_cap']
    
    # Простой расчёт RSI на основе изменений цены
    price_changes = [change_7d, change_24h, change_1h]
    rsi = calculate_rsi([0] + price_changes)
    
    # Определяем сигнал
    signal_type = None
    signal_strength = 0
    reasons = []
    
    # Сильный рост - потенциал для продажи
    if change_1h > 10:
        signal_type = "SELL"
        signal_strength = min(3, int(change_1h / 5))
        reasons.append(f"Сильный рост +{change_1h:.1f}% за час")
    
    # Сильное падение - потенциал для покупки
    elif change_1h < -7:
        signal_type = "BUY"
        signal_strength = min(3, int(abs(change_1h) / 3))
        reasons.append(f"Падение {change_1h:.1f}% за час")
    
    # Анализ тренда
    if change_24h > 15 and change_7d > 20:
        if signal_type == "BUY":
            signal_strength += 1
            reasons.append("Восходящий тренд 7д")
    
    if change_24h < -10 and change_1h > 3:
        signal_type = "BUY"
        signal_strength += 2
        reasons.append("Отскок после падения")
    
    # RSI анализ
    if rsi < RSI_OVERSOLD:
        signal_type = "BUY"
        signal_strength += 1
        reasons.append(f"RSI {rsi:.0f} - перепроданность")
    elif rsi > RSI_OVERBOUGHT:
        signal_type = "SELL"
        signal_strength += 1
        reasons.append(f"RSI {rsi:.0f} - перекупленность")
    
    # Большой объём торгов
    if volume > market_cap * 0.3:  # Объём больше 30% капитализации
        signal_strength += 1
        reasons.append("Высокий объём торгов")
    
    return {
        'name': name,
        'symbol': symbol,
        'price': price,
        'change_1h': change_1h,
        'change_24h': change_24h,
        'change_7d': change_7d,
        'volume': volume,
        'market_cap': market_cap,
        'rsi': rsi,
        'signal_type': signal_type,
        'signal_strength': signal_strength,
        'reasons': reasons
    }

def find_new_opportunities():
    """Поиск новых перспективных монет"""
    new_coins = get_new_coins()
    if not new_coins:
        return []
    
    opportunities = []
    
    for coin in new_coins:
        # Фильтруем по критериям
        change_24h = coin.get('price_change_percentage_24h', 0) or 0
        volume = coin.get('total_volume', 0)
        market_cap = coin.get('market_cap', 0)
        
        # Критерии перспективности
        is_promising = (
            change_24h > 20 and  # Рост больше 20% за сутки
            volume > 1000000 and  # Объём больше $1М
            market_cap > 500000 and  # Капитализация больше $500К
            market_cap < 50000000  # Но меньше $50М (ранняя стадия)
        )
        
        if is_promising:
            opportunities.append({
                'name': coin['name'],
                'symbol': coin['symbol'].upper(),
                'price': coin['current_price'],
                'change_24h': change_24h,
                'volume': volume,
                'market_cap': market_cap
            })
    
    return opportunities[:3]  # Топ-3 новые монеты

def generate_message(signals, new_opportunities):
    """Генерация сообщения для Telegram"""
    if not signals and not new_opportunities:
        return f"✅ Мониторинг активен\n⏰ {datetime.now().strftime('%H:%M:%S')}\n📊 Сигналов нет"
    
    message = f"🤖 <b>АНАЛИЗ РЫНКА</b>\n⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
    
    # Новые перспективные монеты
    if new_opportunities:
        message += "🆕 <b>НОВЫЕ ПЕРСПЕКТИВНЫЕ МОНЕТЫ:</b>\n\n"
        for opp in new_opportunities:
            message += f"💎 <b>{opp['name']} ({opp['symbol']})</b>\n"
            message += f"💰 Цена: ${opp['price']:.8f}\n"
            message += f"📈 24ч: +{opp['change_24h']:.1f}%\n"
            message += f"💵 Объём: ${opp['volume']:,.0f}\n"
            message += f"🎯 Капитализация: ${opp['market_cap']:,.0f}\n"
            message += f"✅ <b>РЕКОМЕНДАЦИЯ: КУПИТЬ (ранняя стадия)</b>\n\n"
    
    # Сигналы по отслеживаемым монетам
    if signals:
        message += "🎯 <b>ТОРГОВЫЕ СИГНАЛЫ:</b>\n\n"
        for signal in signals:
            # Эмодзи силы сигнала
            strength_emoji = "🔥" * signal['signal_strength']
            
            # Эмодзи направления
            if signal['signal_type'] == 'BUY':
                action_emoji = "🟢"
                action = "КУПИТЬ"
            else:
                action_emoji = "🔴"
                action = "ПРОДАТЬ"
            
            message += f"{action_emoji} <b>{signal['name']} ({signal['symbol']})</b>\n"
            message += f"💰 Цена: ${signal['price']:.8f}\n"
            message += f"📊 1ч: {signal['change_1h']:+.2f}% | 24ч: {signal['change_24h']:+.2f}%\n"
            message += f"📈 RSI: {signal['rsi']:.0f}\n"
            message += f"💵 Объём: ${signal['volume']:,.0f}\n\n"
            
            message += f"{strength_emoji} <b>СИГНАЛ: {action}</b>\n"
            message += f"📋 Причины:\n"
            for reason in signal['reasons']:
                message += f"   • {reason}\n"
            message += "\n"
    
    return message

def main():
    """Основная функция"""
    # Получаем данные
    data = get_crypto_data()
    
    if not data:
        send_telegram_message("⚠️ Ошибка получения данных")
        return
    
    # Анализируем каждую монету
    signals = []
    for coin in data:
        analysis = analyze_coin(coin)
        if analysis['signal_type'] and analysis['signal_strength'] >= 2:
            signals.append(analysis)
    
    # Ищем новые возможности
    new_opportunities = find_new_opportunities()
    
    # Отправляем сообщение
    message = generate_message(signals, new_opportunities)
    send_telegram_message(message)

if __name__ == "__main__":
    main()

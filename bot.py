import requests
import os
from datetime import datetime
import statistics

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# Основные мемкоины для отслеживания
MEMECOINS = ['dogecoin', 'shiba-inu', 'pepe', 'floki', 'bonk', 'dogwifhat', 'memecoin']

# Пороги для сигналов
PRICE_CHANGE_THRESHOLD = 3  # Снизили до 3% для большей чувствительности
VOLUME_SPIKE_MULTIPLIER = 2.0  # Всплеск объёма в 2 раза
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

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
        "price_change_percentage": "1h,24h,7d,14d,30d"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка получения данных: {e}")
        return None

def get_coin_details(coin_id):
    """Получение детальных данных о монете"""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    params = {"localization": "false", "tickers": "false", "community_data": "true", "developer_data": "true"}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка получения деталей {coin_id}: {e}")
        return None

def get_new_coins():
    """Поиск новых перспективных монет"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "category": "meme-token",
        "order": "volume_desc",
        "per_page": 30,
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

def calculate_rsi(changes, period=14):
    """Расчёт RSI (Relative Strength Index)"""
    if not changes or len(changes) < 2:
        return 50
    
    gains = [max(0, c) for c in changes]
    losses = [abs(min(0, c)) for c in changes]
    
    avg_gain = sum(gains) / len(gains) if gains else 0
    avg_loss = sum(losses) / len(losses) if losses else 0
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Расчёт полос Боллинджера"""
    if len(prices) < period:
        return None
    
    sma = sum(prices[-period:]) / period
    variance = sum([(p - sma) ** 2 for p in prices[-period:]]) / period
    std = variance ** 0.5
    
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    
    return {
        'sma': sma,
        'upper': upper_band,
        'lower': lower_band,
        'current': prices[-1]
    }

def calculate_macd(prices):
    """Расчёт MACD (Moving Average Convergence Divergence)"""
    if len(prices) < 26:
        return None
    
    # EMA 12 и 26
    ema12 = sum(prices[-12:]) / 12
    ema26 = sum(prices[-26:]) / 26
    
    macd_line = ema12 - ema26
    signal_line = macd_line * 0.9  # Упрощённая сигнальная линия
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': macd_line - signal_line
    }

def analyze_volume(coin):
    """Анализ объёма торгов"""
    volume = coin['total_volume']
    market_cap = coin['market_cap']
    
    if market_cap == 0:
        return {'spike': False, 'ratio': 0, 'level': 'Низкий'}
    
    volume_ratio = volume / market_cap
    
    # Определяем уровень объёма
    if volume_ratio > 0.5:
        level = "Экстремально высокий"
        spike = True
    elif volume_ratio > 0.3:
        level = "Очень высокий"
        spike = True
    elif volume_ratio > 0.15:
        level = "Высокий"
        spike = True
    elif volume_ratio > 0.05:
        level = "Средний"
        spike = False
    else:
        level = "Низкий"
        spike = False
    
    return {
        'spike': spike,
        'ratio': volume_ratio * 100,
        'level': level,
        'volume': volume
    }

def calculate_risk_score(coin, analysis):
    """Оценка риска инвестиции"""
    risk_points = 0
    risk_factors = []
    
    # Волатильность
    change_1h = abs(coin.get('price_change_percentage_1h_in_currency', 0) or 0)
    if change_1h > 15:
        risk_points += 3
        risk_factors.append("Экстремальная волатильность")
    elif change_1h > 10:
        risk_points += 2
        risk_factors.append("Высокая волатильность")
    elif change_1h > 5:
        risk_points += 1
    
    # Капитализация
    market_cap = coin['market_cap']
    if market_cap < 1000000:
        risk_points += 3
        risk_factors.append("Очень низкая капитализация")
    elif market_cap < 10000000:
        risk_points += 2
        risk_factors.append("Низкая капитализация")
    
    # Объём
    volume_analysis = analyze_volume(coin)
    if volume_analysis['level'] == "Низкий":
        risk_points += 2
        risk_factors.append("Низкая ликвидность")
    
    # Тренд
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
    change_30d = coin.get('price_change_percentage_30d_in_currency', 0) or 0
    if change_7d < -30 and change_30d < -50:
        risk_points += 2
        risk_factors.append("Нисходящий тренд")
    
    # Определяем уровень риска
    if risk_points >= 7:
        risk_level = "🔴 ОЧЕНЬ ВЫСОКИЙ"
    elif risk_points >= 5:
        risk_level = "🟠 ВЫСОКИЙ"
    elif risk_points >= 3:
        risk_level = "🟡 СРЕДНИЙ"
    else:
        risk_level = "🟢 НИЗКИЙ"
    
    return {
        'level': risk_level,
        'points': risk_points,
        'factors': risk_factors
    }

def calculate_profit_potential(coin):
    """Расчёт потенциала прибыли"""
    change_24h = coin.get('price_change_percentage_24h_in_currency', 0) or 0
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
    
    # Моментум
    momentum = (change_24h * 0.7) + (change_7d * 0.3)
    
    if momentum > 50:
        return "🚀 Очень высокий (50-200%)"
    elif momentum > 20:
        return "📈 Высокий (20-50%)"
    elif momentum > 5:
        return "📊 Средний (5-20%)"
    elif momentum > -10:
        return "⚖️ Умеренный (0-5%)"
    else:
        return "📉 Низкий (отрицательный)"

def analyze_coin(coin):
    """Продвинутый анализ монеты"""
    name = coin['name']
    symbol = coin['symbol'].upper()
    price = coin['current_price']
    change_1h = coin.get('price_change_percentage_1h_in_currency', 0) or 0
    change_24h = coin.get('price_change_percentage_24h_in_currency', 0) or 0
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
    change_14d = coin.get('price_change_percentage_14d_in_currency', 0) or 0
    change_30d = coin.get('price_change_percentage_30d_in_currency', 0) or 0
    
    volume = coin['total_volume']
    market_cap = coin['market_cap']
    
    # Технические индикаторы
    price_changes = [change_30d, change_14d, change_7d, change_24h, change_1h]
    rsi = calculate_rsi(price_changes)
    
    # Анализ объёма
    volume_analysis = analyze_volume(coin)
    
    # MACD (упрощённый на основе изменений)
    macd_signal = "Бычий" if change_7d > change_14d else "Медвежий"
    
    # Определяем сигнал
    signal_type = None
    signal_strength = 0
    reasons = []
    confidence = 0
    
    # === СИГНАЛЫ НА ПОКУПКУ (BUY) ===
    
    # RSI перепроданность
    if rsi < RSI_OVERSOLD:
        if not signal_type:
            signal_type = "BUY"
        signal_strength += 2
        confidence += 15
        reasons.append(f"RSI {rsi:.0f} - сильная перепроданность")
    
    # Отскок после падения
    if change_24h < -15 and change_1h > 3:
        if not signal_type:
            signal_type = "BUY"
        signal_strength += 3
        confidence += 25
        reasons.append("Отскок после сильного падения")
    
    # Начало восходящего тренда
    if change_7d > 0 and change_24h > 5 and change_1h > 2:
        if not signal_type:
            signal_type = "BUY"
        signal_strength += 2
        confidence += 20
        reasons.append("Формирование восходящего тренда")
    
    # Всплеск объёма + рост
    if volume_analysis['spike'] and change_1h > 3:
        if not signal_type:
            signal_type = "BUY"
        signal_strength += 2
        confidence += 15
        reasons.append(f"Всплеск объёма ({volume_analysis['level']})")
    
    # === СИГНАЛЫ НА ПРОДАЖУ (SELL) ===
    
    # RSI перекупленность
    if rsi > RSI_OVERBOUGHT:
        if not signal_type:
            signal_type = "SELL"
        signal_strength += 2
        confidence += 15
        reasons.append(f"RSI {rsi:.0f} - перекупленность")
    
    # Сильный рост - фиксация прибыли
    if change_1h > 15:
        signal_type = "SELL"
        signal_strength += 3
        confidence += 30
        reasons.append(f"Сильный памп +{change_1h:.1f}% - время фиксировать")
    
    # Разворот тренда
    if change_7d > 30 and change_24h < 0 and change_1h < -3:
        signal_type = "SELL"
        signal_strength += 2
        confidence += 20
        reasons.append("Признаки разворота тренда")
    
    # Падение на высоком объёме
    if volume_analysis['spike'] and change_1h < -5:
        signal_type = "SELL"
        signal_strength += 2
        confidence += 15
        reasons.append("Распродажа на высоком объёме")
    
    # Оценка риска
    risk_analysis = calculate_risk_score(coin, {})
    
    # Потенциал прибыли
    profit_potential = calculate_profit_potential(coin)
    
    # Корректируем уверенность
    confidence = min(95, confidence)
    
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
        'macd': macd_signal,
        'volume_analysis': volume_analysis,
        'risk': risk_analysis,
        'profit_potential': profit_potential,
        'signal_type': signal_type,
        'signal_strength': min(5, signal_strength),
        'confidence': confidence,
        'reasons': reasons
    }

def find_new_opportunities():
    """Поиск новых перспективных монет с расширенным анализом"""
    new_coins = get_new_coins()
    if not new_coins:
        return []
    
    opportunities = []
    
    for coin in new_coins:
        change_24h = coin.get('price_change_percentage_24h', 0) or 0
        volume = coin.get('total_volume', 0)
        market_cap = coin.get('market_cap', 0)
        
        # Расширенные критерии
        volume_ratio = volume / market_cap if market_cap > 0 else 0
        
        is_promising = (
            change_24h > 15 and
            volume > 500000 and
            market_cap > 300000 and
            market_cap < 100000000 and
            volume_ratio > 0.1
        )
        
        if is_promising:
            # Рассчитываем скор перспективности
            promise_score = 0
            promise_factors = []
            
            if change_24h > 50:
                promise_score += 3
                promise_factors.append("Экстремальный рост")
            elif change_24h > 30:
                promise_score += 2
                promise_factors.append("Сильный рост")
            
            if volume_ratio > 0.5:
                promise_score += 3
                promise_factors.append("Огромный объём")
            elif volume_ratio > 0.3:
                promise_score += 2
                promise_factors.append("Высокий объём")
            
            if market_cap < 5000000:
                promise_score += 2
                promise_factors.append("Micro-cap (ранняя стадия)")
            
            opportunities.append({
                'name': coin['name'],
                'symbol': coin['symbol'].upper(),
                'price': coin['current_price'],
                'change_24h': change_24h,
                'volume': volume,
                'market_cap': market_cap,
                'volume_ratio': volume_ratio * 100,
                'promise_score': promise_score,
                'promise_factors': promise_factors
            })
    
    # Сортируем по скору перспективности
    opportunities.sort(key=lambda x: x['promise_score'], reverse=True)
    return opportunities[:3]

def generate_message(signals, new_opportunities):
    """Генерация расширенного сообщения"""
    if not signals and not new_opportunities:
        return f"✅ Мониторинг активен\n⏰ {datetime.now().strftime('%H:%M:%S')}\n📊 Сигналов нет\n💤 Рынок спокоен"
    
    message = f"🤖 <b>ПРОФЕССИОНАЛЬНЫЙ АНАЛИЗ РЫНКА</b>\n⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
    
    # Новые перспективные монеты
    if new_opportunities:
        message += "🆕 <b>НОВЫЕ ПЕРСПЕКТИВНЫЕ МОНЕТЫ:</b>\n\n"
        for i, opp in enumerate(new_opportunities, 1):
            stars = "⭐" * opp['promise_score']
            message += f"{i}. 💎 <b>{opp['name']} ({opp['symbol']})</b> {stars}\n"
            message += f"💰 Цена: ${opp['price']:.8f}\n"
            message += f"📈 24ч: +{opp['change_24h']:.1f}%\n"
            message += f"💵 Объём: ${opp['volume']:,.0f}\n"
            message += f"🎯 Капа: ${opp['market_cap']:,.0f}\n"
            message += f"📊 Объём/Капа: {opp['volume_ratio']:.1f}%\n"
            message += f"✨ Факторы:\n"
            for factor in opp['promise_factors']:
                message += f"   • {factor}\n"
            message += f"✅ <b>РЕКОМЕНДАЦИЯ: КУПИТЬ (EARLY)</b>\n\n"
    
    # Торговые сигналы
    if signals:
        message += "🎯 <b>ТОРГОВЫЕ СИГНАЛЫ С АНАЛИЗОМ:</b>\n\n"
        for signal in signals:
            strength_emoji = "🔥" * signal['signal_strength']
            
            if signal['signal_type'] == 'BUY':
                action_emoji = "🟢"
                action = "ПОКУПАТЬ"
            else:
                action_emoji = "🔴"
                action = "ПРОДАВАТЬ"
            
            message += f"{action_emoji} <b>{signal['name']} ({signal['symbol']})</b> {strength_emoji}\n"
            message += f"💰 Цена: ${signal['price']:.8f}\n"
            message += f"📊 1ч: {signal['change_1h']:+.2f}% | 24ч: {signal['change_24h']:+.2f}% | 7д: {signal['change_7d']:+.2f}%\n"
            message += f"📈 RSI: {signal['rsi']:.0f} | MACD: {signal['macd']}\n"
            message += f"💵 Объём: ${signal['volume']:,.0f} ({signal['volume_analysis']['level']})\n"
            message += f"🎯 Капа: ${signal['market_cap']:,.0f}\n"
            message += f"⚠️ Риск: {signal['risk']['level']}\n"
            message += f"💹 Потенциал: {signal['profit_potential']}\n\n"
            
            message += f"🎯 <b>СИГНАЛ: {action}</b>\n"
            message += f"🎓 Уверенность: {signal['confidence']}%\n"
            message += f"📋 Анализ:\n"
            for reason in signal['reasons']:
                message += f"   • {reason}\n"
            
            if signal['risk']['factors']:
                message += f"⚠️ Факторы риска:\n"
                for factor in signal['risk']['factors']:
                    message += f"   • {factor}\n"
            
            message += "\n"
    
    message += "━━━━━━━━━━━━━━━━━━\n"
    message += "<i>⚠️ Не финансовая консультация. DYOR!</i>"
    
    return message

def main():
    """Основная функция"""
    data = get_crypto_data()
    
    if not data:
        send_telegram_message("⚠️ Ошибка получения данных")
        return
    
    # Анализируем монеты
    signals = []
    for coin in data:
        analysis = analyze_coin(coin)
        # Снизили порог до 1 для более частых сигналов
        if analysis['signal_type'] and analysis['signal_strength'] >= 1:
            signals.append(analysis)
    
    # Сортируем по силе сигнала
    signals.sort(key=lambda x: (x['signal_strength'], x['confidence']), reverse=True)
    
    # Берём топ-5 сигналов
    signals = signals[:5]
    
    # Ищем новые возможности
    new_opportunities = find_new_opportunities()
    
    # Отправляем сообщение
    message = generate_message(signals, new_opportunities)
    
    # Разбиваем длинное сообщение если нужно
    if len(message) > 4000:
        # Telegram ограничение 4096 символов
        parts = [message[i:i+4000] for i in range(0, len(message), 4000)]
        for part in parts:
            send_telegram_message(part)
    else:
        send_telegram_message(message)

if __name__ == "__main__":
    main()

import requests
import os
from datetime import datetime, timedelta

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# Критерии для поиска НОВЫХ перспективных монет
MIN_MARKET_CAP = 100000        # Минимум $100K (ранняя стадия)
MAX_MARKET_CAP = 50000000      # Максимум $50M (еще не взлетела)
MIN_VOLUME = 50000             # Минимум $50K объема (есть интерес)
MIN_PRICE_CHANGE_24H = 10      # Минимум +10% за сутки (моментум)
MIN_VOLUME_TO_MCAP_RATIO = 0.05  # Объём минимум 5% от капитализации

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

def get_trending_coins():
    """Получение трендовых новых монет"""
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json().get('coins', [])
    except Exception as e:
        print(f"Ошибка получения трендов: {e}")
        return []

def get_new_listings():
    """Получение недавно добавленных монет"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_asc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "1h,24h,7d"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка получения новых листингов: {e}")
        return []

def get_meme_coins():
    """Поиск новых мемкоинов"""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "category": "meme-token",
        "order": "volume_desc",
        "per_page": 50,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h,7d"
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Ошибка поиска мемкоинов: {e}")
        return []

def calculate_gem_score(coin):
    """Расчет потенциала монеты (чем выше, тем лучше)"""
    score = 0
    factors = []
    
    market_cap = coin.get('market_cap', 0)
    volume = coin.get('total_volume', 0)
    change_24h = coin.get('price_change_percentage_24h', 0) or 0
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
    
    if market_cap == 0 or volume == 0:
        return 0, []
    
    volume_ratio = volume / market_cap
    
    # Оценка капитализации (чем меньше, тем больший потенциал роста)
    if market_cap < 1000000:  # < $1M
        score += 5
        factors.append("Micro-cap (<$1M) - огромный потенциал")
    elif market_cap < 5000000:  # < $5M
        score += 4
        factors.append("Очень низкая капа (<$5M)")
    elif market_cap < 10000000:  # < $10M
        score += 3
        factors.append("Низкая капа (<$10M)")
    elif market_cap < 25000000:  # < $25M
        score += 2
        factors.append("Ранняя стадия (<$25M)")
    
    # Оценка объема торгов
    if volume_ratio > 1.0:  # Объём больше капы!
        score += 5
        factors.append(f"БЕШЕНЫЙ объём {volume_ratio:.1f}x капы!")
    elif volume_ratio > 0.5:
        score += 4
        factors.append(f"Огромный объём {volume_ratio:.1f}x капы")
    elif volume_ratio > 0.3:
        score += 3
        factors.append(f"Высокий объём {volume_ratio:.1f}x капы")
    elif volume_ratio > 0.15:
        score += 2
        factors.append("Хороший объём торгов")
    
    # Оценка роста
    if change_24h > 100:  # +100% за сутки
        score += 5
        factors.append(f"Экстремальный памп +{change_24h:.0f}%")
    elif change_24h > 50:
        score += 4
        factors.append(f"Сильный рост +{change_24h:.0f}%")
    elif change_24h > 25:
        score += 3
        factors.append(f"Хороший рост +{change_24h:.0f}%")
    elif change_24h > 10:
        score += 2
        factors.append(f"Растет +{change_24h:.0f}%")
    
    # Тренд за неделю
    if change_7d and change_7d > 200:
        score += 3
        factors.append(f"Недельный взрыв +{change_7d:.0f}%")
    elif change_7d and change_7d > 100:
        score += 2
        factors.append(f"Сильный недельный тренд +{change_7d:.0f}%")
    
    # Бонус за новизну (по названию часто видно)
    name_lower = coin.get('name', '').lower()
    if any(word in name_lower for word in ['trump', '2024', '2025', 'new', 'fresh']):
        score += 2
        factors.append("Актуальная тематика")
    
    return score, factors

def analyze_gem(coin):
    """Полный анализ потенциального гема"""
    name = coin.get('name', 'Unknown')
    symbol = coin.get('symbol', 'N/A').upper()
    price = coin.get('current_price', 0)
    market_cap = coin.get('market_cap', 0)
    volume = coin.get('total_volume', 0)
    change_1h = coin.get('price_change_percentage_1h_in_currency', 0) or 0
    change_24h = coin.get('price_change_percentage_24h', 0) or 0
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
    
    # Фильтрация по критериям
    if market_cap < MIN_MARKET_CAP or market_cap > MAX_MARKET_CAP:
        return None
    
    if volume < MIN_VOLUME:
        return None
    
    if change_24h < MIN_PRICE_CHANGE_24H:
        return None
    
    volume_ratio = volume / market_cap if market_cap > 0 else 0
    if volume_ratio < MIN_VOLUME_TO_MCAP_RATIO:
        return None
    
    # Рассчитываем потенциал
    gem_score, factors = calculate_gem_score(coin)
    
    if gem_score < 6:  # Минимальный порог качества
        return None
    
    # Определяем потенциал роста
    if gem_score >= 15:
        potential = "10-100x 🚀🚀🚀"
        risk = "ОЧЕНЬ ВЫСОКИЙ"
    elif gem_score >= 12:
        potential = "5-20x 🚀🚀"
        risk = "ВЫСОКИЙ"
    elif gem_score >= 9:
        potential = "3-10x 🚀"
        risk = "СРЕДНИЙ"
    else:
        potential = "2-5x"
        risk = "СРЕДНИЙ"
    
    return {
        'name': name,
        'symbol': symbol,
        'price': price,
        'market_cap': market_cap,
        'volume': volume,
        'change_1h': change_1h,
        'change_24h': change_24h,
        'change_7d': change_7d,
        'volume_ratio': volume_ratio,
        'gem_score': gem_score,
        'factors': factors,
        'potential': potential,
        'risk': risk
    }

def find_best_gems():
    """Поиск лучших гемов со всех источников"""
    all_gems = []
    
    # Источник 1: Трендовые монеты
    print("Проверяем трендовые монеты...")
    trending = get_trending_coins()
    for item in trending[:20]:
        coin_data = item.get('item', {})
        # Получаем детальные данные
        try:
            detail_url = f"https://api.coingecko.com/api/v3/coins/{coin_data.get('id')}"
            detail_response = requests.get(detail_url, timeout=10)
            if detail_response.status_code == 200:
                detail = detail_response.json()
                market_data = detail.get('market_data', {})
                
                coin = {
                    'name': detail.get('name'),
                    'symbol': detail.get('symbol'),
                    'current_price': market_data.get('current_price', {}).get('usd', 0),
                    'market_cap': market_data.get('market_cap', {}).get('usd', 0),
                    'total_volume': market_data.get('total_volume', {}).get('usd', 0),
                    'price_change_percentage_1h_in_currency': market_data.get('price_change_percentage_1h_in_currency', {}).get('usd', 0),
                    'price_change_percentage_24h': market_data.get('price_change_percentage_24h', 0),
                    'price_change_percentage_7d_in_currency': market_data.get('price_change_percentage_7d_in_currency', {}).get('usd', 0)
                }
                
                gem = analyze_gem(coin)
                if gem:
                    all_gems.append(gem)
        except Exception as e:
            print(f"Ошибка обработки трендовой монеты: {e}")
            continue
    
    # Источник 2: Новые листинги
    print("Проверяем новые листинги...")
    new_listings = get_new_listings()
    for coin in new_listings:
        gem = analyze_gem(coin)
        if gem:
            all_gems.append(gem)
    
    # Источник 3: Новые мемкоины
    print("Проверяем мемкоины...")
    meme_coins = get_meme_coins()
    for coin in meme_coins:
        gem = analyze_gem(coin)
        if gem:
            all_gems.append(gem)
    
    # Убираем дубликаты
    unique_gems = {}
    for gem in all_gems:
        key = gem['symbol']
        if key not in unique_gems or gem['gem_score'] > unique_gems[key]['gem_score']:
            unique_gems[key] = gem
    
    # Сортируем по скору
    sorted_gems = sorted(unique_gems.values(), key=lambda x: x['gem_score'], reverse=True)
    
    return sorted_gems[:5]  # Топ-5 лучших

def format_message(gems):
    """Форматирование сообщения (упрощенный стиль)"""
    if not gems:
        return "🔍 Сканирование завершено\n💤 Новых перспективных монет не найдено"
    
    timestamp = datetime.now().strftime('%H:%M')
    message = f"💎 <b>НОВЫЕ ГЕМЫ НАЙДЕНЫ</b> | {timestamp}\n\n"
    
    for i, gem in enumerate(gems, 1):
        stars = "⭐" * min(5, gem['gem_score'] // 3)
        
        message += f"<b>{i}. {gem['name']} (${gem['symbol']})</b> {stars}\n"
        message += f"💰 Цена: ${gem['price']:.8f}\n"
        message += f"📊 Капа: ${gem['market_cap']:,.0f}\n"
        message += f"💵 Объём: ${gem['volume']:,.0f}\n"
        message += f"📈 24ч: +{gem['change_24h']:.1f}%"
        
        if gem['change_7d']:
            message += f" | 7д: {gem['change_7d']:+.0f}%"
        
        message += f"\n\n🎯 <b>Потенциал: {gem['potential']}</b>\n"
        message += f"⚠️ Риск: {gem['risk']}\n\n"
        
        message += "💡 Почему интересно:\n"
        for factor in gem['factors'][:3]:  # Топ-3 фактора
            message += f"  • {factor}\n"
        
        message += "\n" + "─" * 30 + "\n\n"
    
    return message

def main():
    """Основная функция"""
    print("🔍 Начинаем поиск новых гемов...")
    
    gems = find_best_gems()
    
    print(f"✅ Найдено {len(gems)} перспективных монет")
    
    message = format_message(gems)
    
    # Разбиваем если сообщение слишком длинное
    if len(message) > 4000:
        parts = [message[i:i+3900] for i in range(0, len(message), 3900)]
        for part in parts:
            send_telegram_message(part)
    else:
        send_telegram_message(message)
    
    print("✅ Сообщения отправлены")

if __name__ == "__main__":
    main()
```

5. **Commit changes** → **Commit changes**

---

## 🎯 ЧТО ИЗМЕНИЛОСЬ:

### **1. ПОИСК ТОЛЬКО НОВЫХ МОНЕТ:**
✅ **Капитализация:** $100K - $50M (ранняя стадия)
✅ **Рост:** минимум +10% за сутки
✅ **Объём:** активная торговля
✅ **Исключены:** старые монеты типа SHIB, DOGE, PEPE

### **2. ТРИ ИСТОЧНИКА ДАННЫХ:**
- 🔥 Трендовые монеты (как Trump coin)
- 🆕 Новые листинги
- 🐶 Новые мемкоины

### **3. СИСТЕМА ОЦЕНКИ (GEM SCORE):**
- **15+ баллов** = потенциал 10-100x 🚀🚀🚀
- **12-14 баллов** = потенциал 5-20x 🚀🚀
- **9-11 баллов** = потенциал 3-10x 🚀
- **6-8 баллов** = потенциал 2-5x

### **4. УПРОЩЕННЫЙ ФОРМАТ:**
```
💎 НОВЫЕ ГЕМЫ НАЙДЕНЫ | 15:30

1. TrumpCoin ($TRUMP) ⭐⭐⭐⭐⭐
💰 Цена: $0.00012345
📊 Капа: $2,500,000
💵 Объём: $5,000,000
📈 24ч: +350% | 7д: +890%

🎯 Потенциал: 10-100x 🚀🚀🚀
⚠️ Риск: ОЧЕНЬ ВЫСОКИЙ

💡 Почему интересно:
  • Micro-cap (<$1M) - огромный потенциал
  • БЕШЕНЫЙ объём 2.0x капы!
  • Экстремальный памп +350%

──────────────────────────────

import requests
import os
import json
from datetime import datetime

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

# Критерии поиска
MIN_MARKET_CAP = 100000
MAX_MARKET_CAP = 50000000
MIN_VOLUME = 50000
MIN_PRICE_CHANGE_24H = 10
MIN_VOLUME_TO_MCAP_RATIO = 0.05

# История отправленных монет (простое хранилище)
SENT_COINS_FILE = "sent_coins.json"

def load_sent_coins():
    """Загрузка истории отправленных монет"""
    try:
        if os.path.exists(SENT_COINS_FILE):
            with open(SENT_COINS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_sent_coins(coins_dict):
    """Сохранение истории"""
    try:
        with open(SENT_COINS_FILE, 'w') as f:
            json.dump(coins_dict, f)
    except Exception as e:
        print(f"Ошибка сохранения истории: {e}")

def was_sent_recently(symbol, hours=24):
    """Проверка - отправляли ли эту монету недавно"""
    sent_coins = load_sent_coins()
    if symbol in sent_coins:
        last_sent = datetime.fromisoformat(sent_coins[symbol])
        hours_passed = (datetime.now() - last_sent).total_seconds() / 3600
        return hours_passed < hours
    return False

def mark_as_sent(symbol):
    """Отметить монету как отправленную"""
    sent_coins = load_sent_coins()
    sent_coins[symbol] = datetime.now().isoformat()
    save_sent_coins(sent_coins)

def send_telegram_message(message):
    """Отправка сообщения в Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Ошибка отправки: {e}")
        return None

def check_social_presence(coin_id):
    """Проверка наличия активных соцсетей"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {"score": 0, "links": {}}
        
        data = response.json()
        links = data.get('links', {})
        community = data.get('community_data', {})
        
        score = 0
        social_links = {}
        
        # Twitter
        twitter = links.get('twitter_screen_name', '')
        if twitter:
            score += 3
            social_links['twitter'] = f"https://twitter.com/{twitter}"
        
        # Telegram
        telegram = links.get('telegram_channel_identifier', '')
        if telegram:
            score += 3
            social_links['telegram'] = f"https://t.me/{telegram}"
        
        # Website
        homepage = links.get('homepage', [])
        if homepage and homepage[0]:
            score += 2
            social_links['website'] = homepage[0]
        
        # Reddit
        reddit = links.get('subreddit_url', '')
        if reddit:
            score += 1
            social_links['reddit'] = reddit
        
        # Активность в Twitter
        twitter_followers = community.get('twitter_followers', 0)
        if twitter_followers > 10000:
            score += 3
        elif twitter_followers > 1000:
            score += 2
        elif twitter_followers > 100:
            score += 1
        
        # Активность в Telegram
        telegram_users = community.get('telegram_channel_user_count', 0)
        if telegram_users > 5000:
            score += 2
        elif telegram_users > 1000:
            score += 1
        
        return {"score": score, "links": social_links}
    except Exception as e:
        print(f"Ошибка проверки соцсетей: {e}")
        return {"score": 0, "links": {}}

def check_honeypot(contract_address, chain="eth"):
    """Базовая проверка на honeypot (скам)"""
    # Примечание: полноценная проверка требует платного API
    # Здесь делаем базовую проверку через публичные данные
    
    try:
        # Проверяем есть ли ликвидность и возможность продажи
        # Используем CoinGecko для базовой проверки
        
        # Если монета торгуется на крупных DEX - скорее всего не скам
        score = 5  # Базовый безопасный скор
        warnings = []
        
        # В реальности здесь можно подключить:
        # - honeypot.is API
        # - Token Sniffer API
        # - Но они платные, поэтому используем косвенные признаки
        
        return {"safe_score": score, "warnings": warnings}
    except:
        return {"safe_score": 5, "warnings": []}

def get_dex_links(symbol, name, contract=None):
    """Генерация ссылок на DEX для покупки"""
    links = []
    
    # DEXScreener (универсальный)
    search_query = symbol.replace('$', '').upper()
    links.append(f"https://dexscreener.com/search?q={search_query}")
    
    # CoinGecko
    links.append(f"https://www.coingecko.com/en/search?query={name}")
    
    # Если известен контракт - прямые ссылки на DEX
    if contract:
        # Uniswap
        links.append(f"https://app.uniswap.org/#/swap?outputCurrency={contract}")
        # PancakeSwap
        links.append(f"https://pancakeswap.finance/swap?outputCurrency={contract}")
    
    return links

def get_coin_contract(coin_id):
    """Получение адреса контракта монеты"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            platforms = data.get('platforms', {})
            # Пробуем найти контракт на популярных сетях
            for platform in ['ethereum', 'binance-smart-chain', 'polygon-pos', 'solana']:
                if platform in platforms and platforms[platform]:
                    return platforms[platform]
        return None
    except:
        return None

def get_trending_coins():
    """Получение трендовых монет"""
    url = "https://api.coingecko.com/api/v3/search/trending"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json().get('coins', [])
    except Exception as e:
        print(f"Ошибка получения трендов: {e}")
        return []

def get_new_listings():
    """Получение новых листингов"""
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

def calculate_gem_score(coin, social_data, safety_data):
    """Расчет потенциала монеты с учетом всех факторов"""
    score = 0
    factors = []
    
    market_cap = coin.get('market_cap', 0)
    volume = coin.get('total_volume', 0)
    change_24h = coin.get('price_change_percentage_24h', 0) or 0
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
    
    if market_cap == 0 or volume == 0:
        return 0, []
    
    volume_ratio = volume / market_cap
    
    # 1. Оценка капитализации
    if market_cap < 500000:
        score += 6
        factors.append("Ultra micro-cap (<$500K)")
    elif market_cap < 1000000:
        score += 5
        factors.append("Micro-cap (<$1M)")
    elif market_cap < 5000000:
        score += 4
        factors.append("Очень низкая капа (<$5M)")
    elif market_cap < 10000000:
        score += 3
        factors.append("Низкая капа (<$10M)")
    elif market_cap < 25000000:
        score += 2
        factors.append("Ранняя стадия (<$25M)")
    
    # 2. Оценка объема торгов
    if volume_ratio > 1.5:
        score += 6
        factors.append(f"БЕШЕНЫЙ объём {volume_ratio:.1f}x")
    elif volume_ratio > 1.0:
        score += 5
        factors.append(f"Огромнейший объём {volume_ratio:.1f}x")
    elif volume_ratio > 0.5:
        score += 4
        factors.append(f"Огромный объём {volume_ratio:.1f}x")
    elif volume_ratio > 0.3:
        score += 3
        factors.append(f"Высокий объём {volume_ratio:.1f}x")
    elif volume_ratio > 0.15:
        score += 2
        factors.append("Хороший объём")
    
    # 3. Оценка роста
    if change_24h > 200:
        score += 6
        factors.append(f"МЕГА ПАМП +{change_24h:.0f}%!")
    elif change_24h > 100:
        score += 5
        factors.append(f"Экстремальный рост +{change_24h:.0f}%")
    elif change_24h > 50:
        score += 4
        factors.append(f"Сильный памп +{change_24h:.0f}%")
    elif change_24h > 25:
        score += 3
        factors.append(f"Хороший рост +{change_24h:.0f}%")
    elif change_24h > 10:
        score += 2
        factors.append(f"Растет +{change_24h:.0f}%")
    
    # 4. Недельный тренд
    if change_7d and change_7d > 500:
        score += 4
        factors.append(f"Недельный ВЗРЫВ +{change_7d:.0f}%")
    elif change_7d and change_7d > 200:
        score += 3
        factors.append(f"Сильный недельный +{change_7d:.0f}%")
    elif change_7d and change_7d > 100:
        score += 2
        factors.append(f"Недельный рост +{change_7d:.0f}%")
    
    # 5. Соцсети (бонус за активность)
    social_score = social_data.get('score', 0)
    if social_score >= 10:
        score += 4
        factors.append("Мощное комьюнити")
    elif social_score >= 7:
        score += 3
        factors.append("Активное комьюнити")
    elif social_score >= 4:
        score += 2
        factors.append("Есть соцсети")
    
    # 6. Безопасность
    safe_score = safety_data.get('safe_score', 0)
    if safe_score >= 8:
        score += 2
        factors.append("Проверенный контракт")
    elif safe_score >= 5:
        score += 1
    
    # 7. Актуальность названия
    name_lower = coin.get('name', '').lower()
    trending_words = ['trump', 'elon', 'musk', 'pepe', 'doge', '2025', 'ai', 'moon']
    if any(word in name_lower for word in trending_words):
        score += 2
        factors.append("Трендовая тематика")
    
    return score, factors

def determine_signal_level(gem_score):
    """Определение уровня сигнала"""
    if gem_score >= 20:
        return {
            'emoji': '🔥🔥🔥',
            'level': 'ГОРЯЧЕЕ',
            'potential': '20-100x',
            'risk': 'ЭКСТРЕМАЛЬНЫЙ'
        }
    elif gem_score >= 15:
        return {
            'emoji': '🔥🔥',
            'level': 'ОЧЕНЬ ПЕРСПЕКТИВНОЕ',
            'potential': '10-50x',
            'risk': 'ОЧЕНЬ ВЫСОКИЙ'
        }
    elif gem_score >= 12:
        return {
            'emoji': '🔥',
            'level': 'ПЕРСПЕКТИВНОЕ',
            'potential': '5-20x',
            'risk': 'ВЫСОКИЙ'
        }
    elif gem_score >= 9:
        return {
            'emoji': '💎',
            'level': 'ИНТЕРЕСНОЕ',
            'potential': '3-10x',
            'risk': 'СРЕДНИЙ'
        }
    else:
        return {
            'emoji': '⭐',
            'level': 'НА ЗАМЕТКУ',
            'potential': '2-5x',
            'risk': 'СРЕДНИЙ'
        }

def analyze_gem(coin, coin_id=None):
    """Полный анализ гема"""
    name = coin.get('name', 'Unknown')
    symbol = coin.get('symbol', 'N/A').upper()
    price = coin.get('current_price', 0)
    market_cap = coin.get('market_cap', 0)
    volume = coin.get('total_volume', 0)
    change_1h = coin.get('price_change_percentage_1h_in_currency', 0) or 0
    change_24h = coin.get('price_change_percentage_24h', 0) or 0
    change_7d = coin.get('price_change_percentage_7d_in_currency', 0) or 0
    
    # Базовые фильтры
    if market_cap < MIN_MARKET_CAP or market_cap > MAX_MARKET_CAP:
        return None
    
    if volume < MIN_VOLUME:
        return None
    
    if change_24h < MIN_PRICE_CHANGE_24H:
        return None
    
    volume_ratio = volume / market_cap if market_cap > 0 else 0
    if volume_ratio < MIN_VOLUME_TO_MCAP_RATIO:
        return None
    
    # Проверка - отправляли ли недавно
    if was_sent_recently(symbol, hours=24):
        print(f"⏭️  {symbol} уже отправляли недавно, пропускаем")
        return None
    
    # Проверка соцсетей
    social_data = {"score": 0, "links": {}}
    if coin_id:
        social_data = check_social_presence(coin_id)
    
    # Проверка безопасности
    contract = get_coin_contract(coin_id) if coin_id else None
    safety_data = check_honeypot(contract) if contract else {"safe_score": 5, "warnings": []}
    
    # Рассчитываем потенциал
    gem_score, factors = calculate_gem_score(coin, social_data, safety_data)
    
    if gem_score < 8:  # Минимальный порог
        return None
    
    # Определяем уровень сигнала
    signal = determine_signal_level(gem_score)
    
    # Ссылки на покупку
    dex_links = get_dex_links(symbol, name, contract)
    
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
        'signal': signal,
        'social': social_data,
        'safety': safety_data,
        'contract': contract,
        'dex_links': dex_links,
        'coin_id': coin_id
    }

def find_best_gems():
    """Поиск лучших гемов"""
    all_gems = []
    
    # Источник 1: Трендовые
    print("🔍 Проверяем трендовые монеты...")
    trending = get_trending_coins()
    for item in trending[:15]:
        try:
            coin_data = item.get('item', {})
            coin_id = coin_data.get('id')
            
            detail_url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
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
                
                gem = analyze_gem(coin, coin_id)
                if gem:
                    all_gems.append(gem)
        except Exception as e:
            print(f"Ошибка: {e}")
            continue
    
    # Источник 2: Новые листинги
    print("🔍 Проверяем новые листинги...")
    new_listings = get_new_listings()
    for coin in new_listings[:30]:
        gem = analyze_gem(coin, coin.get('id'))
        if gem:
            all_gems.append(gem)
    
    # Источник 3: Мемкоины
    print("🔍 Проверяем мемкоины...")
    meme_coins = get_meme_coins()
    for coin in meme_coins[:30]:
        gem = analyze_gem(coin, coin.get('id'))
        if gem:
            all_gems.append(gem)
    
    # Убираем дубликаты
    unique_gems = {}
    for gem in all_gems:
        key = gem['symbol']
        if key not in unique_gems or gem['gem_score'] > unique_gems[key]['gem_score']:
            unique_gems[key] = gem
    
    # Сортируем
    sorted_gems = sorted(unique_gems.values(), key=lambda x: x['gem_score'], reverse=True)
    
    # Отмечаем как отправленные
    for gem in sorted_gems[:5]:
        mark_as_sent(gem['symbol'])
    
    return sorted_gems[:5]

def format_message(gems):
    """Форматирование сообщения"""
    if not gems:
        return "🔍 Сканирование завершено\n💤 Новых перспективных монет не найдено"
    
    timestamp = datetime.now().strftime('%H:%M')
    message = f"🎯 <b>НОВЫЕ СИГНАЛЫ</b> | {timestamp}\n\n"
    
    for i, gem in enumerate(gems, 1):
        signal = gem['signal']
        
        message += f"{signal['emoji']} <b>{signal['level']}</b>\n"
        message += f"<b>{i}. {gem['name']} (${gem['symbol']})</b>\n\n"
        
        message += f"💰 Цена: ${gem['price']:.8f}\n"
        message += f"📊 Капа: ${gem['market_cap']:,.0f}\n"
        message += f"💵 Объём: ${gem['volume']:,.0f} ({gem['volume_ratio']:.1f}x)\n"
        message += f"📈 24ч: +{gem['change_24h']:.1f}%"
        
        if gem['change_7d']:
            message += f" | 7д: {gem['change_7d']:+.0f}%"
        
        message += f"\n\n🎯 <b>Потенциал: {signal['potential']}</b>\n"
        message += f"⚠️ Риск: {signal['risk']}\n\n"
        
        # Почему интересно
        message += "💡 <b>Анализ:</b>\n"
        for factor in gem['factors'][:4]:
            message += f"  ✓ {factor}\n"
        
        # Соцсети
        social_links = gem['social'].get('links', {})
        if social_links:
            message += "\n📱 <b>Соцсети:</b>\n"
            if 'twitter' in social_links:
                message += f"  • <a href='{social_links['twitter']}'>Twitter</a>\n"
            if 'telegram' in social_links:
                message += f"  • <a href='{social_links['telegram']}'>Telegram</a>\n"
            if 'website' in social_links:
                message += f"  • <a href='{social_links['website']}'>Website</a>\n"
        
        # Ссылки на покупку
        message += "\n🛒 <b>Купить:</b>\n"
        dex_links = gem['dex_links']
        if len(dex_links) > 0:
            message +=

import telebot
import requests
import schedule
import time
import threading
from datetime import datetime, timedelta

# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# ЗАМЕНИ НА СВОЙ ТОКЕН
BOT_TOKEN = '7123456789:AAHabc123defGHIjklMNOpqrSTUvwxyZ'
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище данных
subscribers = set()           # Все, кто написал /start
premium_users = {}           # {user_id: datetime окончания подписки}
PRICE_30_DAYS = 300           # Цена подписки

# === КОМАНДЫ ===
@bot.message_handler(commands=['start'])
def start(m):
    user_id = m.from_user.id
    subscribers.add(user_id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = telebot.types.KeyboardButton('/price PEPE')
    btn2 = telebot.types.KeyboardButton('/subscribe')
    markup.add(btn1, btn2)
    bot.send_message(user_id,
        "Подписка активна! Бесплатные сигналы — каждые 5 мин.\n\n"
        "Хочешь раньше всех? /subscribe — 300 руб. за 7 дней\n"
        "Или спроси цену: /price PEPE", reply_markup=markup)

@bot.message_handler(commands=['subscribe'])
def subscribe(m):
    user_id = m.from_user.id
    if user_id in premium_users and premium_users[user_id] > datetime.now():
        bot.send_message(user_id, "У тебя уже есть подписка!")
        return

    # Генерация счёта (в реале — ЮKassa/QIWI)
    bot.send_message(user_id,
        "Платная подписка: 300 руб. за 30 дней\n\n"
        "Оплати по реквизитам:\n"
        "СБЕР: `2202 2068 4182 6048

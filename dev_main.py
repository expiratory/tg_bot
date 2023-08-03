import telebot
import datetime
import pickle
from decimal import Decimal
import re

bot = telebot.TeleBot('TG_BOT_API_KEY')


def load_time_tracking():
    try:
        with open('time_tracking.pkl', 'rb') as file:
            return pickle.load(file)
    except (FileNotFoundError, EOFError):
        return {}


def save_time_tracking(time_tracking_dict):
    with open('time_tracking.pkl', 'wb') as file:
        pickle.dump(time_tracking_dict, file)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.from_user.id, 'Привет! Я бот, в котором можно трекать рабочее время \n'
                                           'Чтобы узнать список доступных команд - напиши /help \n')


@bot.message_handler(commands=['help'])
def helper(message):
    bot.send_message(message.from_user.id, 'Вот список моих функций: \n'
                                           '1. Если ты хочешь затрекать время - просто напиши его в том же формате как в Jira \n')


def parse_time_input(input_str):
    hours_pattern = r'(\d+(\.\d+)?)\s*h'
    minutes_pattern = r'(\d+)\s*m'
    days_pattern = r'(\d+(\.\d+)?)\s*d'

    total_hours = 0

    hours_match = re.search(hours_pattern, input_str)
    if hours_match:
        hours = float(hours_match.group(1))
        total_hours += hours

    minutes_match = re.search(minutes_pattern, input_str)
    if minutes_match:
        minutes = int(minutes_match.group(1))
        total_hours += minutes / 60

    days_match = re.search(days_pattern, input_str)
    if days_match:
        days = float(days_match.group(1))
        total_hours += days * 8

    return Decimal(total_hours)


def format_time(hours):
    total_minutes = int(hours * 60)

    days = total_minutes // (60 * 8)
    hours -= days * 8
    hours = int(hours)
    minutes = total_minutes - days * 60 * 8 - hours * 60

    formatted_time = ""
    if days > 0:
        formatted_time += f"{days}d "
    if hours > 0:
        formatted_time += f"{hours}h "
    if minutes > 0:
        formatted_time += f"{minutes}m"

    return formatted_time.strip()


@bot.message_handler(content_types=['text'])
def time_track(message):
    user_id = message.from_user.id
    time_tracking_dict = load_time_tracking()

    if user_id not in time_tracking_dict:
        time_tracking_dict[user_id] = (Decimal('8'), datetime.date.today())

    time_tracking, last_update_date = time_tracking_dict[user_id]

    time_input = message.text.lower()
    time = parse_time_input(time_input)
    if time_tracking < time:
        if time_tracking <= 0.0001:
            bot.send_message(message.from_user.id, 'Ты уже затрекал за сегодня все время')
        else:
            formatted_time_tracking = format_time(time_tracking)
            bot.send_message(message.from_user.id,
                             f'Слишком много хочешь затрекать, тебе осталось затрекать только {formatted_time_tracking}')
    elif time_tracking >= time:
        time_tracking -= time
        if time == 0:
            bot.send_message(message.from_user.id,
                             'Либо ты ввел 0, либо ты ввел данные в неправильном формате. Давай попробуем заново')
        elif time_tracking == 0:
            bot.send_message(message.from_user.id, 'Ты затрекал за сегодня все время, красавчик')
        else:
            formatted_time = format_time(time)
            formatted_time_tracking = format_time(time_tracking)
            bot.send_message(message.from_user.id,
                             f'Ты затрекал {formatted_time}, значит тебе осталось затрекать {formatted_time_tracking}')

    now = datetime.datetime.now()

    if now.date() > last_update_date:
        time_tracking = 8.0
        last_update_date = now.date()

    time_tracking_dict[user_id] = (time_tracking, last_update_date)
    save_time_tracking(time_tracking_dict)


bot.polling(non_stop=True, interval=0)

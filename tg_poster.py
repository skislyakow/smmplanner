import os
import requests
from dotenv import load_dotenv

load_dotenv()

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHANNEL_ID = os.getenv('TG_CHANNEL_ID')


def tg_create_post(message, photo_url=None):
    if photo_url:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
        params = {"chat_id": TG_CHANNEL_ID, "caption": message, "photo": photo_url}
    else:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TG_CHANNEL_ID, "text": message}

    response = requests.post(url, data=params)
    data = response.json()

    if data.get("ok"):
        return data["result"]["message_id"]
    else:
        raise Exception(f"Telegram API error: {data}")


def tg_delete_post(message_id):
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/deleteMessage"
    params = {"chat_id": TG_CHANNEL_ID, "message_id": message_id}
    requests.post(url, data=params)
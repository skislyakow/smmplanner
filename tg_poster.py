import os
import requests
from dotenv import load_dotenv

load_dotenv()

TG_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
TG_CHANNEL_ID = os.getenv('TG_CHANNEL_ID')

# Проверить def _make_request
# Добавлено / Начало
def _make_request(url, params):
    """Внутренний хелпер для безопасного выполнения запросов."""
    try:
        # timeout=10 защищает от бесконечного зависания при обрыве связи
        response = requests.post(url, data=params, timeout=10)
        response.raise_for_status() 
        return response.json()

    except requests.exceptions.Timeout:
        raise Exception("Ошибка: Время ожидания ответа от Telegram истекло (Timeout).")
    except requests.exceptions.ConnectionError:
        raise Exception("Ошибка: Нет соединения с интернетом или сервер Telegram недоступен.")
    except requests.exceptions.HTTPError as http_err:
        raise Exception(f"HTTP ошибка: Сервер вернул код {response.status_code}. Текст: {http_err}")
    except requests.exceptions.RequestException as err:
        raise Exception(f"Непредвиденная сетевая ошибка: {err}")
# Добавлено / Конец

def tg_create_post(message, photo_url=None):
    """Создает пост в Тelegram канале (с фото или без)."""
    if photo_url:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
        params = {"chat_id": TG_CHANNEL_ID, "caption": message, "photo": photo_url}
    else:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TG_CHANNEL_ID, "text": message}

    data = _make_request(url, params)  # Добавлено

    if data.get("ok"):
        return data["result"]["message_id"]
    else:
        raise Exception(f"Telegram API error: {data}")


def tg_delete_post(message_id):
    """Удаляет пост из Telegram канала по его message_id."""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/deleteMessage"
    params = {"chat_id": TG_CHANNEL_ID, "message_id": message_id}

    data = _make_request(url, params)  # Добавлено

    if not data.get("ok"):  # Добавлено
        raise Exception(f"Telegram API error: {data}")  # Добавлено

    return True  # Добавлено / проверить на что необходимо возвращать

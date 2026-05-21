import os
from dotenv import load_dotenv
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError


def send_telegram_post(text: str, image_urls_list: str) -> list[int]:
    """
    Отправляет пост в Telegram и возвращает список ID сообщений..
    Конфиденциальные данные забираются из файла .env.
    """
    load_dotenv()

    tg_token = os.getenv("TELEGRAM_TOKEN")
    tg_chatid = os.getenv("TELEGRAM_CHAT_ID")

    if not tg_token or not tg_chatid:
        print("[Ошибка TG]: Настройки не найдены в .env!")
        return []

    try:
        bot = Bot(token=tg_token)

        # Превращаем строку с запятыми в список чистых ссылок
        images = [url.strip() for url in image_urls_list.split(",") if url.strip()]

        # Вариант 1: Только текст (лимит до 4096 символов)
        # """parse_mode (str) - Send Markdown or HTML, if you want Telegram apps to show bold, italic,
        # fixed-width text or inline URLs in your bot’s message. """
        if not images:
            msg = bot.send_message(chat_id=tg_chatid, text=text, parse_mode='HTML')
            return [msg.message_id]

        # Вариант 2: Одна картинка с подписью (лимит текста до 1024 символов)
        elif len(images) == 1:
            msg = bot.send_photo(chat_id=tg_chatid, photo=images[0], caption=text, parse_mode='HTML')
            return [msg.message_id]

        # Вариант 3: Альбом из нескольких картинок (до 10 штук, текст в первой)
        else:
            media_group = []
            for i, url in enumerate(images[:10]):  # Срез защищает от лимитов API / must include 2–10 items
                if i == 0:
                    media_group.append(InputMediaPhoto(media=url, caption=text, parse_mode='HTML'))
                else:
                    media_group.append(InputMediaPhoto(media=url))

            messages = bot.send_media_group(chat_id=tg_chatid, media=media_group)
            return [msg.message_id for msg in messages]

    except TelegramError as e:
        print(f"[Ошибка Telegram API при отправке]: {e}")
        return []

# (Work in progress) Функция ниже набросок "Удаление поста по ID" 
# def delete_telegram_post(message_ids_list: str | int) -> bool:

#     """Удаляет один опубликованный пост (принимает строку с ID через запятую)."""
#     load_dotenv()

#     tg_token = os.getenv("TELEGRAM_TOKEN")
#     tg_chatid = os.getenv("TELEGRAM_CHAT_ID")

#     if not tg_token or not tg_chatid:
#         return False

#     try:
#         ids_to_delete = [int(i.strip()) for i in str(message_ids_list).split(",") if i.strip()]
#     except ValueError:
#         print(f"[Ошибка TG]: Неверный формат ID для удаления: {message_ids_list}")
#         return False

#     if not ids_to_delete:
#         return False

#     try:
#         bot = Bot(token=tg_token)
#         for msg_id in ids_to_delete:
#             bot.delete_message(chat_id=tg_chatid, message_id=msg_id)
#         print(f"Пост ID {ids_to_delete} удален из Telegram.")
#         return True
#     except TelegramError as e:
#         print(f"[Ошибка Telegram API при удалении {ids_to_delete}]: {e}")
#         if "message to delete not found" in str(e).lower():
#             return True
#         return False
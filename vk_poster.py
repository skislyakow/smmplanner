import os

from datetime import datetime

import requests
import vk_api


VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_USER_TOKEN = os.getenv("VK_USER_TOKEN")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID"))


vk_group_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
vk_group = vk_group_session.get_api()

vk_user_session = vk_api.VkApi(token=VK_USER_TOKEN)
vk_user = vk_user_session.get_api()


def parse_date(date_str):
    """Преобразует строку даты в datetime. Форматы: ДД.ММ.ГГГГ ЧЧ:ММ"""
    date_str = date_str.strip()
    for fmt in ["%d.%m.%Y - %H:%M", "%d.%m.%Y %H:%M", "%d.%m.%Y"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Неверный формат даты: {date_str}")


def upload_photo_to_wall(photo_url):
    """Загружает фото на стену VK, возвращает attachment строку или None"""
    upload_server = vk_user.photos.getWallUploadServer(owner_id=VK_GROUP_ID)
    upload_url = upload_server["upload_url"]
    try:
        photo_data = requests.get(photo_url).content
    except requests.RequestException:
        return None
    files = {"photo": ("photo.jpg", photo_data, "image/jpeg")}

    upload_response = requests.post(upload_url, files=files, timeout=10)
    try:
        upload_result = upload_response.json()
    except ValueError:
        return None

    if "photo" not in upload_result:
        return None
    try:
        saved_photo = vk_user.photos.saveWallPhoto(
            owner_id=VK_GROUP_ID,
            server=upload_result["server"],
            photo=upload_result["photo"],
            hash=upload_result["hash"],
        )[0]
    except vk_api.exceptions.VkApiError:
        return None

    return f"photo{saved_photo['owner_id']}_{saved_photo['id']}"


def vk_create_post(text, photo_url=None, publish_date=None):
    """Публикует пост VK (сразу или отложенно). Возвращает post_id или None"""
    if photo_url:
        attachment = upload_photo_to_wall(photo_url)
        if attachment is None:
            return None
    else:
        attachment = None

    kwargs = {
        "owner_id": VK_GROUP_ID,
        "message": text,
        "attachment": attachment,
    }

    if publish_date and isinstance(publish_date, str):
        try:
            publish_date = parse_date(publish_date)
            kwargs["publish_date"] = int(publish_date.timestamp())
        except ValueError as error:
            print(f"Ошибка даты: {error}")

    result = vk_group.wall.post(**kwargs)
    return result["post_id"]


def vk_delete_post(post_id):
    """Удаляет пост VK по post_id с помощью токена пользователя"""
    vk_user.wall.delete(owner_id=VK_GROUP_ID, post_id=post_id)

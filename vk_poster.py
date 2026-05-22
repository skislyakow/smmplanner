import os

# import json
from datetime import datetime


from dotenv import load_dotenv
import requests
import vk_api

# import google_sheet
# from google_sheet import update_vk_status


load_dotenv()

VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_USER_TOKEN = os.getenv("VK_USER_TOKEN")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID"))


vk_group_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
vk_group = vk_group_session.get_api()

vk_user_session = vk_api.VkApi(token=VK_USER_TOKEN)
vk_user = vk_user_session.get_api()


# def load_posts(path="posts.json"):
#    with open(path, encoding="utf-8") as file:
#        return json.load(file)
#
#
# def get_vk_posts(posts):
#    result = []
#    for post in posts:
#        if post["vk"]["send"] and not post["vk"]["status"]:
#            result.append(post)
#    return result


# def is_time_to_publish(publish_date_str):
#    pub_date = parse_date(publish_date_str)
#    return datetime.now() >= pub_date


def parse_date(date_str):
    date_str = date_str.strip()
    for fmt in ["%d.%m.%Y - %H:%M", "%d.%m.%Y %H:%M", "%d.%m.%Y"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Неверный формат даты: {date_str}")


def upload_photo_to_wall(photo_url):
    upload_server = vk_user.photos.getWallUploadServer(owner_id=VK_GROUP_ID)
    upload_url = upload_server["upload_url"]

    photo_data = requests.get(photo_url).content
    files = {"photo": ("photo.jpg", photo_data, "image/jpeg")}

    upload_result = requests.post(upload_url, files=files).json()

    if "photo" not in upload_result:
        print(f"Ошибка загрузки фото: {photo_url[:60]}")
        return None
    try:
        saved_photo = vk_user.photos.saveWallPhoto(
            owner_id=VK_GROUP_ID,
            server=upload_result["server"],
            photo=upload_result["photo"],
            hash=upload_result["hash"],
        )[0]
    except vk_api.exceptions.VkApiError as error:
        print(f"Ошибка сохранения фото: {error}")
        return None

    return f"photo{saved_photo['owner_id']}_{saved_photo['id']}"


def create_post(text, photo_url=None, publish_date=None):
    if photo_url:
        attachment = upload_photo_to_wall(photo_url)
        if attachment is None:
            print("Фото не загружено — пост не опубликован")
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


def delete_post(post_id):
    vk_user.wall.delete(owner_id=VK_GROUP_ID, post_id=post_id)
    print(f"Пост {post_id} успешно удалён")


# def check_deletions(posts):
#    for post in posts:
#        if not post["delete"]:
#            continue
#        if not post["vk"]["post_id"]:
#            continue
#        delete_date_str = post["delete_date"]
#        if delete_date_str:
#            try:
#                delete_date = parse_date(delete_date_str)
#                if datetime.now() < delete_date:
#                    continue
#            except ValueError:
#                continue
#
#        delete_post(int(post["vk"]["post_id"]))
#        post["vk"]["status"] = "удалён"
#        post["vk"]["post_id"] = ""
#        update_vk_status(post["row"], "удалён", "")


# if __name__ == "__main__":
#    google_sheet.main()
#    posts = load_posts()
#    vk_posts = get_vk_posts(posts)
#    print(f"Всего постов: {len(posts)}, для VK: {len(vk_posts)}")
#
#    for post in vk_posts:
#        pub_date_str = post["publish_date"]
#
#        if pub_date_str and parse_date(pub_date_str) > datetime.now():
#            publish_date = pub_date_str
#        else:
#            publish_date = None
#        post_id = create_post(post["text"], post["photo_url"], publish_date)
#
#        if post_id:
#            update_vk_status(post["row"], "опубликовано", post_id)
#            post["vk"]["status"] = "опубликовано"
#        else:
#            update_vk_status(post["row"], "ошибка фото", "")
#            post["vk"]["status"] = "ошибка фото"
#
#    print("\nПроверяю посты на удаление...")
#    check_deletions(posts)
#
#    with open("posts.json", "w", encoding="utf-8") as f:
#        json.dump(posts, f, ensure_ascii=False, indent=2)

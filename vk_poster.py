import os

from dotenv import load_dotenv
import vk_api
import requests


load_dotenv()

VK_GROUP_TOKEN = os.getenv("VK_GROUP_TOKEN")
VK_USER_TOKEN = os.getenv("VK_USER_TOKEN")
VK_GROUP_ID = os.getenv("VK_GROUP_ID")


vk_group_session = vk_api.VkApi(token=VK_GROUP_TOKEN)
vk_group = vk_group_session.get_api()

vk_user_session = vk_api.VkApi(token=VK_USER_TOKEN)
vk_user = vk_user_session.get_api()


def upload_photo_to_wall(photo_url):
    upload_server = vk_user.photos.getWallUploadServer(owner_id=VK_GROUP_ID)
    upload_url = upload_server["upload_url"]

    photo_data = requests.get(photo_url).content
    files = {"photo": ("photo.jpg", photo_data, "image/jpeg")}

    upload_result = requests.post(upload_url, files=files).json()

    saved_photo = vk_user.photos.saveWallPhoto(
        owner_id=VK_GROUP_ID,
        server=upload_result["server"],
        photo=upload_result["photo"],
        hash=upload_result["hash"],
    )[0]

    return f"photo{saved_photo['owner_id']}_{saved_photo['id']}"


def create_post(text, photo_url):
    if photo_url:
        attachment = upload_photo_to_wall(photo_url)
    else:
        attachment = None

    result = vk_group.wall.post(
        owner_id=VK_GROUP_ID, message=text, attachment=attachment
    )
    return result["post_id"]


if __name__ == "__main__":
    text = "Тестовый пост с фото"
    photo_url = "https://amournsk.ru/upload/medialibrary/f43/f4354e1263bef30293879a313092b2ca.jpg"

    post_id = create_post(text, photo_url)
    print(f"Пост опубликован! ID: {post_id}")

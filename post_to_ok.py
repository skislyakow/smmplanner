import os
import json
import hashlib
import time
from datetime import datetime

import requests
from dotenv import load_dotenv


def make_signature(params, secret_key):
    sorted_keys = sorted(params.keys())
    param_string = '|'.join([f"{k}={params[k]}" for k in sorted_keys])
    sign_string = param_string + '|' + secret_key
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest()


def api_request(method, params, public_key, secret_key, access_token):
    full_params = {
        "application_key": public_key,
        "method": method,
        "access_token": access_token,
        "format": "json",
        **params
    }
    full_params["sig"] = make_signature(full_params, secret_key)

    response = requests.post("https://api.ok.ru/fb.do", params=full_params)
    response.raise_for_status()
    return response.json()


def post_to_ok(message, photo_url=None):
    media = [{"type": "text", "text": message}]

    if photo_url:
        media.append({"type": "link", "url": photo_url})

    post_id = api_request(
        "mediatopic.post",
        {
            "gid": group_gid,
            "type": "GROUP_THEME",
            "attachment": json.dumps({"media": media}, ensure_ascii=False)
        },
        public_key, secret_key, access_token
    )

    print(f"Пост опубликован! ID: {post_id}")
    return post_id


def delete_post(post_id):
    api_request(
        "mediatopic.deleteTopic",
        {
            "gid": group_gid,
            "topic_id": str(post_id)
        },
        public_key, secret_key, access_token
    )

    print(f'Пост удалён! ID: {post_id}')


def schedule_action(message, photo_url=None, publish_time=None, delete_time=None):
    if publish_time:
        now = datetime.now()
        wait_seconds = (publish_time - now).total_seconds()
        if wait_seconds > 0:
            print(f"До публикации: {wait_seconds:.0f} секунд")
            time.sleep(wait_seconds)

        post_id = post_to_ok(message, photo_url)

    if delete_time:
        now = datetime.now()
        wait_seconds = (delete_time - now).total_seconds()
        if wait_seconds > 0:
            print(f"До удаления: {wait_seconds:.0f} секунд")
            time.sleep(wait_seconds)

        delete_post(post_id)


if __name__ == '__main__':
    load_dotenv()

    public_key = os.getenv('PUBLIC_KEY')
    secret_key = os.getenv('SECRET_KEY')
    group_gid = os.getenv('GROUP_GID')
    access_token = os.getenv('ACCESS_TOKEN')

    publish_time = datetime(2026, 5, 20, 18, 0, 0)
    delete_time = datetime(2026, 5, 20, 18, 1, 0)

    schedule_action(
        'тест',
        'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSsmbZ_DFjpgEhgr9U547CMfh9YNljR_KtgVQ&s',
        publish_time,
        delete_time
    )

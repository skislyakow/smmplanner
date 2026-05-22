import os
import json
import hashlib
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

from google_sheet import SHEET_ID, get_sheet_data, parse_records, get_client, update_ok_status


def make_signature(params, ok_secret_key):
    sorted_keys = sorted(params.keys())
    param_string = '|'.join([f"{k}={params[k]}" for k in sorted_keys])
    sign_string = param_string + '|' + ok_secret_key
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest()


def api_request(method, params, ok_public_key, ok_secret_key, ok_access_token):
    full_params = {
        "application_key": ok_public_key,
        "method": method,
        "access_token": ok_access_token,
        "format": "json",
        **params
    }
    full_params["sig"] = make_signature(full_params, ok_secret_key)

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
            "gid": ok_group_gid,
            "type": "GROUP_THEME",
            "attachment": json.dumps({"media": media}, ensure_ascii=False)
        },
        ok_public_key, ok_secret_key, ok_access_token
    )

    print(f"Пост опубликован! ID: {post_id}")
    return post_id


def delete_post(post_id):
    api_request(
        "mediatopic.deleteTopic",
        {
            "gid": ok_group_gid,
            "topic_id": str(post_id)
        },
        ok_public_key, ok_secret_key, ok_access_token
    )

    print(f"Пост удалён! ID: {post_id}")


def process_all_posts(posts):
    published = []

    for i, post in enumerate(posts):
        for pub in published[:]:
            if pub['delete_time'] and pub['delete_time'] <= datetime.now():
                print(f"\nВремя удалить пост {pub['post_id']}")
                try:
                    delete_post(pub['post_id'])
                    update_ok_status(worksheet, pub['row'], "удалён", pub['post_id'])
                    published.remove(pub)
                except Exception as e:
                    print(f"Ошибка удаления: {e}")

        print(f"Пост {i + 1}/{len(posts)}")

        if post['publish_time']:
            now = datetime.now()
            wait_seconds = (post['publish_time'] - now).total_seconds()

            if wait_seconds > 0:
                print(f"Публикация: {post['publish_time']}")

                while wait_seconds > 0:
                    sleep_time = min(10, wait_seconds)
                    time.sleep(sleep_time)
                    wait_seconds -= sleep_time

                    for pub in published[:]:
                        if pub['delete_time'] and pub['delete_time'] <= datetime.now():
                            print(f"\nВремя удалить пост {pub['post_id']}")
                            try:
                                delete_post(pub['post_id'])
                                update_ok_status(worksheet, pub['row'], "удалён", pub['post_id'])
                                published.remove(pub)
                            except Exception as e:
                                print(f"Ошибка удаления: {e}")
            else:
                print("Время публикации уже прошло, публикую сразу")

        try:
            post_id = post_to_ok(post['message'], post['photo_url'])
            published.append({
                'row': post['row'],
                'post_id': post_id,
                'delete_time': post['delete_time']
            })
            update_ok_status(worksheet, post['row'], "опубликован", post_id)

            if post['delete_time']:
                update_ok_status(worksheet, post['row'], "ожидает удаления", post_id)

        except Exception as e:
            print(f"Ошибка публикации: {e}")
            update_ok_status(worksheet, post['row'], "не опубликован", "")

    if published:
        for pub in published:
            if pub['delete_time']:
                now = datetime.now()
                wait_seconds = (pub['delete_time'] - now).total_seconds()

                if wait_seconds > 0:
                    print(f"До удаления поста {pub['post_id']}: {wait_seconds:.0f} сек")
                    time.sleep(wait_seconds)
                else:
                    print("Время удаления прошло, удаляю сразу")

                try:
                    delete_post(pub['post_id'])
                    update_ok_status(worksheet, pub['row'], "удалён", pub['post_id'])
                except Exception as e:
                    print(f"Ошибка удаления: {e}")


def filter_posts_for_platform(platform, all_posts):
    posts = []
    for p in all_posts:
        if p[platform]['send'] and p[platform]['status'] != 'Опубликовано':
            if p[platform]['status'] in ['опубликован', 'удалён']:
                continue

            publish_time = None
            if p['publish_date']:
                    publish_time = datetime.strptime(str(p['publish_date']), '%d.%m.%Y %H:%M')

            delete_time = None
            if p['delete'] and p['delete_date']:
                delete_time = datetime.strptime(str(p['delete_date']), '%d.%m.%Y %H:%M')

            posts.append({
                'row': p['row'],
                'message': p['text'],
                'photo_url': p['photo_url'] if p['photo_url'] else None,
                'publish_time': publish_time,
                'delete_time': delete_time,
            })

    return posts


def run_ok_posting():
    print("Загружаю посты из таблицы")
    client = get_client()
    records = get_sheet_data(client)
    all_posts = parse_records(records)

    posts = filter_posts_for_platform('ok', all_posts)

    if not posts:
        print("Нет постов для публикации")
    else:
        print(f"\nНайдено постов: {len(posts)}")
        print("Запуск")
        process_all_posts(posts)
        print("Все посты обработаны!")


if __name__ == '__main__':
    load_dotenv()

    ok_public_key = os.getenv('PUBLIC_KEY_OK')
    ok_secret_key = os.getenv('SECRET_KEY_OK')
    ok_group_gid = os.getenv('GROUP_GID_OK')
    ok_access_token = os.getenv('ACCESS_TOKEN_OK')

    client = get_client()
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.get_worksheet(0)

    run_ok_posting()

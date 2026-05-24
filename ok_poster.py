import os
import json
import hashlib

import requests
from dotenv import load_dotenv


load_dotenv()

ok_public_key = os.getenv('PUBLIC_KEY_OK')
ok_secret_key = os.getenv('SECRET_KEY_OK')
ok_group_gid = os.getenv('GROUP_GID_OK')
ok_access_token = os.getenv('ACCESS_TOKEN_OK')


def make_signature(params, ok_secret_key):
    """Генерирует MD5-подпись для запроса к OK API."""
    sorted_keys = sorted(params.keys())
    param_string = '|'.join([f"{k}={params[k]}" for k in sorted_keys])
    sign_string = param_string + '|' + ok_secret_key
    return hashlib.md5(sign_string.encode('utf-8')).hexdigest()


def api_request(method, params, ok_public_key, ok_secret_key, ok_access_token):
    """Выполняет запрос к OK API с обработкой ошибок"""
    full_params = {
        "application_key": ok_public_key,
        "method": method,
        "access_token": ok_access_token,
        "format": "json",
        **params
    }
    full_params["sig"] = make_signature(full_params, ok_secret_key)

    try:
        response = requests.post("https://api.ok.ru/fb.do", params=full_params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error_code" in data:
            raise Exception(f"OK API error [{data['error_code']}]: {data.get('error_msg', 'Unknown')}")

        return data
    except requests.exceptions.Timeout:
        raise Exception("OK API: Превышено время ожидания (30 сек)")
    except requests.exceptions.ConnectionError:
        raise Exception("OK API: Нет соединения с сервером")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"OK API HTTP ошибка: {e}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"OK API сетевая ошибка: {e}")
    except json.JSONDecodeError:
        raise Exception("OK API: Некорректный JSON в ответе")


def ok_create_post(message, photo_url=None):
    """Публикует пост в OK. Возвращает post_id или None"""
    media = [{"type": "text", "text": message}]

    if photo_url:
        media.append({"type": "link", "url": photo_url})

    try:
        post_id = api_request(
            "mediatopic.post",
            {
                "gid": ok_group_gid,
                "type": "GROUP_THEME",
                "attachment": json.dumps({"media": media}, ensure_ascii=False)
            },
            ok_public_key, ok_secret_key, ok_access_token
        )
        return post_id
    except Exception as e:
        print(f"[OK] Ошибка публикации: {e}")
        raise


def ok_delete_post(post_id):
    """Удаляет пост в OK по post_id"""
    try:
        api_request(
            "mediatopic.deleteTopic",
            {
                "gid": ok_group_gid,
                "topic_id": str(post_id)
            },
            ok_public_key, ok_secret_key, ok_access_token
        )
    except Exception as e:
        print(f"[OK] Ошибка удаления: {e}")
        raise

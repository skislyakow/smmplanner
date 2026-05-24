import os
import json
import hashlib

import requests


ok_public_key = os.getenv("PUBLIC_KEY_OK")
ok_secret_key = os.getenv("SECRET_KEY_OK")
ok_group_gid = os.getenv("GROUP_GID_OK")
ok_access_token = os.getenv("ACCESS_TOKEN_OK")


def make_signature(params, ok_secret_key):
    sorted_keys = sorted(params.keys())
    param_string = "|".join([f"{k}={params[k]}" for k in sorted_keys])
    sign_string = param_string + "|" + ok_secret_key
    return hashlib.md5(sign_string.encode("utf-8")).hexdigest()


def api_request(method, params, ok_public_key, ok_secret_key, ok_access_token):
    full_params = {
        "application_key": ok_public_key,
        "method": method,
        "access_token": ok_access_token,
        "format": "json",
        **params,
    }
    full_params["sig"] = make_signature(full_params, ok_secret_key)

    response = requests.post("https://api.ok.ru/fb.do", params=full_params)
    response.raise_for_status()
    return response.json()


def ok_create_post(message, photo_url=None):
    media = [{"type": "text", "text": message}]

    if photo_url:
        media.append({"type": "link", "url": photo_url})

    post_id = api_request(
        "mediatopic.post",
        {
            "gid": ok_group_gid,
            "type": "GROUP_THEME",
            "attachment": json.dumps({"media": media}, ensure_ascii=False),
        },
        ok_public_key,
        ok_secret_key,
        ok_access_token,
    )

    return post_id


def ok_delete_post(post_id):
    api_request(
        "mediatopic.deleteTopic",
        {"gid": ok_group_gid, "topic_id": str(post_id)},
        ok_public_key,
        ok_secret_key,
        ok_access_token,
    )

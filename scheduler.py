import time
from datetime import datetime

import google_sheet
from vk_poster import parse_date, create_post, delete_post


def publish_vk(post):
    text = post["text"]
    photo_url = post["photo_url"] or None
    publish_date = post["publish_date"] or None
    if publish_date:
        dt = parse_date(publish_date)
        if dt and dt <= datetime.now():
            publish_date = None
    for attempt in range(3):
        try:
            post_id = create_post(text, photo_url, publish_date)
            if post_id:
                google_sheet.update_vk_status(
                    post["row"], "опубликовано", post_id
                )
                return
        except Exception as e:
            if attempt == 2:
                google_sheet.update_vk_status(post["row"], f"ошибка: {e}", "")
                return
            time.sleep(10)


def delete_vk(post):
    delete_date = parse_date(post["delete_date"])
    if delete_date and datetime.now() >= delete_date:
        try:
            delete_post(int(post["vk"]["post_id"]))
            google_sheet.update_vk_status(post["row"], "удалён", "")
        except Exception as e:
            print(f"Ошибка удаления строки {post['row']}: {e}")


def main():
    print("Scheduler запущен")
    while True:
        try:
            records = google_sheet.get_sheet_data()
            posts = google_sheet.parse_records(records)
            for post in posts:
                if post["vk"]["send"] and not post["vk"]["status"]:
                    publish_vk(post)
                if post["delete"] and post["vk"]["post_id"]:
                    delete_vk(post)
        except Exception as e:
            print(f"Ошибка: {e}")
        time.sleep(60)


if __name__ == "__main__":
    main()

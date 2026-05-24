import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from google_sheet import (
    get_sheet_and_data,
    parse_records,
    update_cells,
    update_status,
)
from vk_poster import parse_date, vk_create_post, vk_delete_post
from ok_poster import ok_create_post, ok_delete_post
from tg_poster import tg_create_post, tg_delete_post


def log(msg):
    """Вывод с временной меткой"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


def publish_post(sheet, post, cell_list):
    text = post["text"]
    photo_url = post["photo_url"] or None
    publish_date = post["publish_date"] or None

    if publish_date:
        dt = parse_date(publish_date)
        if dt and dt > datetime.now():
            return
        publish_date = None

    if post["vk"]["send"] and not post["vk"]["status"]:
        for attempt in range(3):
            try:
                post_id = vk_create_post(text, photo_url, publish_date)
                if post_id:
                    update_status(
                        sheet,
                        "vk",
                        post["row"],
                        "опубликовано",
                        post_id,
                        cell_list,
                    )
                    log(f"[VK] Опубликовано: {post_id}")
                    break
            except Exception as e:
                if attempt == 2:
                    update_status(
                        sheet, "vk", post["row"], f"ошибка: {e}", "", cell_list
                    )
                    log(f"[VK] Ошибка: {e}")
                time.sleep(5)
        else:  # выполняется если break не сработал
            if not post_id:
                update_status(
                    sheet, "vk", post["row"], "ошибка фото", "", cell_list
                )
                log("[VK] Ошибка: фото не загрузилось после 3 попыток")

    if post["ok"]["send"] and not post["ok"]["status"]:
        for attempt in range(3):
            try:
                post_id = ok_create_post(text, photo_url)
                if post_id:
                    update_status(
                        sheet,
                        "ok",
                        post["row"],
                        "опубликован",
                        post_id,
                        cell_list,
                    )
                    log(f"[OK] Опубликовано: {post_id}")
                    break
            except Exception as e:
                if attempt == 2:
                    update_status(
                        sheet, "ok", post["row"], f"ошибка: {e}", "", cell_list
                    )
                    log(f"[OK] Ошибка: {e}")
                time.sleep(5)

    if post["tg"]["send"] and not post["tg"]["status"]:
        for attempt in range(3):
            try:
                post_id = tg_create_post(text, photo_url)
                if post_id:
                    update_status(
                        sheet,
                        "tg",
                        post["row"],
                        "опубликован",
                        post_id,
                        cell_list,
                    )
                    log(f"[TG] Опубликовано: {post_id}")
                    break
            except Exception as e:
                if attempt == 2:
                    update_status(
                        sheet, "tg", post["row"], f"ошибка: {e}", "", cell_list
                    )
                    log(f"[TG] Ошибка: {e}")
                time.sleep(5)


def delete_post(sheet, post, cell_list):
    if post["delete_date"]:
        delete_date = parse_date(post["delete_date"])
        if datetime.now() < delete_date:
            return

    vk_id = str(post["vk"]["post_id"]).strip()
    if vk_id and post["vk"]["status"] == "опубликовано":
        try:
            vk_delete_post(vk_id)
            update_status(sheet, "vk", post["row"], "удалён", "", cell_list)
            log(f"[VK] Удалён: {vk_id}")
        except Exception as e:
            log(f"[VK] Ошибка удаления: {e}")

    ok_id = str(post["ok"]["post_id"]).strip()
    if ok_id and post["ok"]["status"] == "опубликован":
        try:
            ok_delete_post(ok_id)
            update_status(sheet, "ok", post["row"], "удалён", "", cell_list)
            log(f"[OK] Удалён: {ok_id}")
        except Exception as e:
            log(f"[OK] Ошибка удаления: {e}")

    tg_id = str(post["tg"]["post_id"]).strip()
    if tg_id and post["tg"]["status"] == "опубликован":
        try:
            tg_delete_post(tg_id)
            update_status(sheet, "tg", post["row"], "удалён", "", cell_list)
            log(f"[TG] Удалён: {tg_id}")
        except Exception as e:
            log(f"[TG] Ошибка удаления: {e}")


def main():
    log("Scheduler Запущен (VK + OK + TG)")
    log("Интервал проверки: 30 сек\n")

    idle_cycles = 0

    while True:
        try:
            sheet, records = get_sheet_and_data()
            if not sheet or records is None:
                log("Сбой подключения. Повтор через 30 сек")
                time.sleep(30)
                continue

            posts = parse_records(records)
            cells_to_update = []

            for post in posts:
                if (
                    (post["vk"]["send"] and not post["vk"]["status"])
                    or (post["ok"]["send"] and not post["ok"]["status"])
                    or (post["tg"]["send"] and not post["tg"]["status"])
                ):
                    publish_post(sheet, post, cells_to_update)

                if post["delete"] and (
                    post["vk"]["post_id"]
                    or post["ok"]["post_id"]
                    or post["tg"]["post_id"]
                ):
                    delete_post(sheet, post, cells_to_update)

            if cells_to_update:
                update_cells(sheet, cells_to_update)

        except Exception as e:
            log(f"Ошибка: {e}")

        idle_cycles += 1
        if not cells_to_update and idle_cycles % 6 == 0:
            log("Скрипт работает. Новых постов нет")
        time.sleep(30)


if __name__ == "__main__":
    main()

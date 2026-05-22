import re
import json
from pathlib import Path
import time
import gspread


SHEET_ID = "1STS2n8ffi7c1aAY16oGxghlJ1qkbDfMK8OZXTnJEo3g"
SERVICE_ACCOUNT_PATH = Path(__file__).parent / "service_account.json"



def make_text_beautiful(text):
    text = re.sub(r' +', ' ', text)
    text = re.sub(r' - ', ' — ', text)
    text = re.sub(r'(^|\s)"', r'\1«', text)
    text = re.sub(r'"($|\s|[\.,!\?])', r'»\1', text)
    
    return text.strip()


def get_client():
    if not SERVICE_ACCOUNT_PATH.exists():
        raise FileNotFoundError(
            f"Файл {SERVICE_ACCOUNT_PATH} не найден. "
            "Положите service_account.json в папку проекта"
        )
    return gspread.service_account(filename=str(SERVICE_ACCOUNT_PATH))


def get_sheet_data(client=None, worksheet_index=0):
    if client is None:
        client = get_client()

    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.get_worksheet(worksheet_index)

    records = worksheet.get_all_records()
    return records


def parse_records(records):
    result = []
    for i, row in enumerate(records):
        raw_text = row.get("Текст поста", "")
        beautiful_text = make_text_beautiful(raw_text)
        post = {
            "row": i + 2,
            "vk": {
                "send": _bool(row.get("VK Отправить")),
                "status": row.get("VK Статус", ""),
                "post_id": row.get("VK id", ""),
            },
            "ok": {
                "send": _bool(row.get("OK Отправить")),
                "status": row.get("OK Статус", ""),
                "post_id": row.get("OK id", ""),
            },
            "tg": {
                "send": _bool(row.get("TG Отправить")),
                "status": row.get("TG Статус", ""),
                "post_id": row.get("TG id", ""),
            },
            "text": beautiful_text,
            "photo_url": row.get("Фото поста", ""),
            "publish_date": row.get("Дата публикации", ""),
            "delete": _bool(row.get("Удалить")),
            "delete_date": row.get("Дата удаления", ""),
        }
        result.append(post)
    return result


def _bool(value):
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ("1", "yes", "true", "да", "+")
    return bool(value)


def save_to_json(data, path="posts.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Сохранено {len(data)} записей в {path}")


def update_vk_status(row, status, post_id=""):
    client = get_client()
    sheet = client.open_by_key(SHEET_ID)
    ws = sheet.get_worksheet(0)
    ws.update_acell(f"B{row}", status)
    ws.update_acell(f"C{row}", str(post_id))


def update_ok_status(worksheet, row, status, post_id):
    worksheet.update(values=[[status]], range_name=f'E{row}')
    if post_id:
        worksheet.update(values=[[str(post_id)]], range_name=f'F{row}')


def update_tg_status(worksheet, row, status, post_id):
    worksheet.update(values=[[status]], range_name=f'H{row}')
    if post_id:
        worksheet.update(values=[[str(post_id)]], range_name=f'I{row}')


def main():
    print("Подключаюсь к Google Sheets...")
    client = get_client()
    records = get_sheet_data(client)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.get_worksheet(0)
    posts = parse_records(records)
    save_to_json(posts)
    # Логику обработи будем дописывать позже
    # print("\nНачинаю обработку строк...")
    # for p in posts:
    #     row_num = p["row"]
    #     print(f"Проверка строки {row_num}: {p['text'][:20]}...")


if __name__ == "__main__":
    main()

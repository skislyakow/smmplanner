import re
import json
from pathlib import Path
import gspread

SHEET_ID = "1STS2n8ffi7c1aAY16oGxghlJ1qkbDfMK8OZXTnJEo3g"
SERVICE_ACCOUNT_PATH = Path(__file__).parent / "service_account.json"
WORKSHEET_INDEX = 0
# Колонки для каждой платформы: (статус, id)
PLATFORM_COLS = {
    "vk": ("B", "C"),
    "ok": ("E", "F"),
    "tg": ("H", "I"),
}


def make_text_beautiful(text):
    text = re.sub(r" +", " ", text)
    text = re.sub(r" - ", " — ", text)
    text = re.sub(r'(^|\s)"', r"\1«", text)
    text = re.sub(r'"($|\s|[\.,!\?])', r"»\1", text)
    return text.strip()


def get_client():
    if not SERVICE_ACCOUNT_PATH.exists():
        raise FileNotFoundError(
            f"Файл {SERVICE_ACCOUNT_PATH} не найден. "
            "Положите service_account.json в папку проекта"
        )
    return gspread.service_account(filename=str(SERVICE_ACCOUNT_PATH))


def get_sheet_and_data():
    try:
        client = get_client()
        if not client:
            return None, None
        sheet = client.open_by_key(SHEET_ID).get_worksheet(WORKSHEET_INDEX)
        records = sheet.get_all_records()
        return sheet, records
    except Exception as e:
        print(f"Ошибка получения данных из Google: {e}")
        return None, None


def update_cells(sheet, cell_objects):
    """Массовое обновление ячеек одним запросом"""
    if sheet and cell_objects:
        try:
            sheet.update_cells(cell_objects)
        except Exception as e:
            print(f"Ошибка при обновлении ячеек: {e}")


def update_status(sheet, platform, row, status, post_id, cell_list):
    """Единая функция для обновления статуса любой платформы"""
    col_status, col_id = PLATFORM_COLS[platform]
    cell_status = sheet.acell(f"{col_status}{row}")
    cell_status.value = status
    cell_list.append(cell_status)
    cell_id = sheet.acell(f"{col_id}{row}")
    cell_id.value = str(post_id)
    cell_list.append(cell_id)


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

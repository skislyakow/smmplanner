import re
import json
from pathlib import Path
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


def update_vk_status(ws, row, status, post_id=""):
    cell_status = ws.acell(f"B{row}")
    cell_status.value = status
    cells_to_update = [cell_status]
    
    if post_id:
        cell_id = ws.acell(f"C{row}")
        cell_id.value = str(post_id)
        cells_to_update.append(cell_id)
        
    ws.update_cells(cells_to_update)


def update_ok_status(ws, row, status, post_id=""):
    cell_status = ws.acell(f"E{row}")
    cell_status.value = status
    cells_to_update = [cell_status]
    
    if post_id:
        cell_id = ws.acell(f"F{row}")
        cell_id.value = str(post_id)
        cells_to_update.append(cell_id)
        
    ws.update_cells(cells_to_update)


def update_tg_status(ws, row, status, post_id=""):
    cell_status = ws.acell(f"H{row}")
    cell_status.value = status
    cells_to_update = [cell_status]
    
    if post_id:
        cell_id = ws.acell(f"I{row}")
        cell_id.value = str(post_id)
        cells_to_update.append(cell_id)
        
    ws.update_cells(cells_to_update)

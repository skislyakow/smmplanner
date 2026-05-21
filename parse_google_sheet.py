import json
import csv
from io import StringIO

import requests


def parse_google_sheet(sheet_id, gid='0'):
    csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
    response = requests.get(csv_url)
    response.raise_for_status()
    response.encoding = 'utf-8'

    reader = csv.DictReader(StringIO(response.text))
    data = list(reader)

    return json.dumps(data, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    sheet_id = "1STS2n8ffi7c1aAY16oGxghlJ1qkbDfMK8OZXTnJEo3g"
    data = parse_google_sheet(sheet_id)
    print(data)

    #with open('data.json', 'w', encoding='utf-8') as f:
    #   f.write(data)
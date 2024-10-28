import os
import json
import requests
import inspect


REQUEST_HEADERS = {
    "accept": "*/*",
    "accept-language": "en,en-US;q=0.9,en-GB;q=0.8,en-HK;q=0.7,zh-HK;q=0.6,zh;q=0.5",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest",
    "Referrer-Policy": "no-referrer-when-downgrade",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
}


def fetch(url: str, params: dict = {}, log_print=True) -> dict | list | str:
    if log_print:
        print(
            f'\033[93m[{inspect.stack()[1][3]}] Fetching data from: ' + url + '\x1b[0m')
    response = requests.request(
        method=params.get("method", "GET"),
        url=url,
        headers=params.get("headers", REQUEST_HEADERS),
        data=params.get("body", None),
    )
    if not response.ok:
        if log_print:
            print(
                f'\033[31m[{inspect.stack()[1][3]}] Failed Fetching data from: ' + url + '\x1b[0m')
        return "Failed to get data from url"
    try:
        return json.loads(response.content.decode('utf-8'))
    except:
        return response.content.decode('utf-8')


def create_folder_if_not_exists(folder_path: str, log_print=True):
    if not os.path.exists(folder_path):
        if log_print:
            print(
                f'\033[31m[{inspect.stack()[1][3]}] Folder {folder_path} does not exist, creating\x1b[0m')
        os.makedirs(folder_path)


def write_json_file(data: dict | list, path: str, log_print=True) -> None:
    create_folder_if_not_exists(os.path.dirname(path))
    if log_print:
        print(
            f'\033[31m[{inspect.stack()[1][3]}] Writing data to {path}\x1b[0m')
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def read_json_file(path: str,  log_print=True) -> dict | list | None:
    if log_print:
        print(
            f'\033[31m[{inspect.stack()[1][3]}] Trying to read data from {path}\x1b[0m')
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return None


def write_file(data: str, path: str, log_print=True):
    create_folder_if_not_exists(os.path.dirname(path))
    if log_print:
        print(
            f'\033[31m[{inspect.stack()[1][3]}] Trying to read data from {path}\x1b[0m')
    with open(path, 'w') as f:
        f.write(data)

import os
import json
import requests
import logging


logger = logging.getLogger(__name__)


def setLogger(external_logger: logging.Logger) -> None:
    """
    Set the logger for the module.

    :param external_logger: The external logger to use.
    """
    global logger
    logger = external_logger


REQUEST_HEADERS = {
    "accept": "application/json",
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}


def fetch(url: str, params: dict = {}) -> dict | list | str:
    logger.info(f"Fetching data from: {url}")
    response = requests.request(
        method=params.get("method", "GET"),
        url=url,
        headers=params.get("headers", REQUEST_HEADERS),
        data=params.get("body", None),
    )
    if not response.ok:
        logger.error(f'Failed Fetching data from: {url}')
        return "Failed to get data from url"
    try:
        responseContent = response.content
        decodedContent = responseContent.decode("utf-8")
        return json.loads(decodedContent)
    except json.decoder.JSONDecodeError:
        return response.content.decode("utf-8")
    except Exception as e:
        if os.path.exists("./errors"):
            with open("./errors/last.txt", 'w') as f:
                f.write(str(responseContent))
            with open("./errors/last-dev.txt", 'w') as f:
                f.write(str(decodedContent))
            logger.error(f'Failed Decoding data from: {url}: Error: {e}')


def create_folder_if_not_exists(folder_path: str):
    if not os.path.exists(folder_path):
        logger.info(f"Folder {folder_path} does not exist, creating")
        os.makedirs(folder_path)


def write_json_file(data: dict | list, path: str) -> None:
    create_folder_if_not_exists(os.path.dirname(path))
    logger.info(f"Writing data to {path}")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def read_json_file(path: str) -> dict | list | None:
    logger.info(f"Trying to read data from {path}")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading data from {path}")
        return None


def write_file(data: str, path: str):
    create_folder_if_not_exists(os.path.dirname(path))
    logger.info(f" Writing data to {path}")
    with open(path, 'w', encoding="utf-8-sig") as f:
        f.write(data)


def read_file(path: str):
    logger.info(f"Trying to read data from {path}")
    try:
        with open(path, 'r', encoding="utf-8-sig") as f:
            return f.read()
    except:
        return None

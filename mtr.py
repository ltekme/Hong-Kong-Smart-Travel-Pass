import os
import json
import requests

from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator

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
    "Referrer-Policy": "no-referrer-when-downgrade"
}


def fetch(url: str, params: dict = {}) -> dict | list:
    print("Fetching data from:", url)
    return json.loads(requests.request(
        method=params.get("method", "GET"),
        url=url,
        headers=params.get("headers", REQUEST_HEADERS),
        data=params.get("body", None),
    ).content)


class MTRApi():

    queryColumns = "`Chinese Name`,`English Name`,`Station Code`,`Line Code`,`Station ID`, `Sequence` as `Line Station Sequence`"

    def __init__(self, credentials: Credentials) -> None:
        self.credentials = credentials
        self.table_name = f"{credentials.project_id}.Transport.MTR"

    @staticmethod
    def listdictify_query(results: RowIterator):
        return [{column.name: station[column.name] for column in results.schema
                 } for station in results]

    @staticmethod
    def prettify_station(stations: list[dict[str, str]] | dict[str, str]) -> str:
        if type(stations) is not list:
            stations = [stations]
        headers = ",".join(stations[0].keys())
        values = "\n".join(
            [",".join(str(value) for value in station.values()) for station in stations])
        return f"{headers}\n{values}"

    def get_station_from_station_id(self, station_id: str) -> dict[str, str]:
        client = bigquery.Client(credentials=self.credentials)
        query = client.query(f"""
SELECT {self.queryColumns} FROM `{self.table_name}`
WHERE
    `Station ID` = '{station_id}'
;""")
        results = query.result()
        return self.listdictify_query(results)[0]

    def get_station_from_station_code(self, station_code: str) -> dict[str, str]:
        client = bigquery.Client(credentials=self.credentials)
        query = client.query(f"""
SELECT {self.queryColumns} FROM `{self.table_name}`
WHERE
    `Station Code` = '{station_code}'
;""")
        results = query.result()
        return self.listdictify_query(results)[0]

    @property
    def stations(self) -> list[dict[str, str]]:
        client = bigquery.Client(credentials=self.credentials)
        query = client.query(f"""
SELECT DISTINCT {self.queryColumns} FROM `{self.table_name}` ORDER BY `Station ID`
;""")
        results = query.result()
        return self.listdictify_query(results)


if __name__ == "__main__":
    credentials = Credentials.from_service_account_file('gcp_cred-data.json')
    mtr = MTRApi(credentials=credentials)
    # print(mtr.stations)
    # station = mtr.get_station_from_station_code("AWE")
    print(mtr.prettify_station(mtr.stations))

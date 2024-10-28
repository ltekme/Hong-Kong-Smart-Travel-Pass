import os
import json
import requests

from google.oauth2.service_account import Credentials
from google.cloud import bigquery
from google.cloud.bigquery.table import RowIterator
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

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


def fetch(url: str, params: dict = {}) -> dict | list:
    print("Fetching data from:", url)
    return json.loads(requests.request(
        method=params.get("method", "GET"),
        url=url,
        headers=params.get("headers", REQUEST_HEADERS),
        data=params.get("body", None),
    ).content)


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


def write_data(data: dict | list, path: str) -> None:
    print("Writing data to:", path)
    create_folder_if_not_exists(os.path.dirname(path))
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def read_json_file(file_path: str) -> dict | list:
    print("Reading data from:", file_path)
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except:
        return []


class MTRApi():

    station_data_path = "mtr_data/mtr_stations.json"
    chroma_db_path = "./mtr_chroma_db"
    chroma_db_collection = "mtr"
    mtr_data_csv = "./data/mtr_lines_and_stations.csv"
    queryColumns = "`Chinese Name`,`English Name`,`Station Code`,`Line Code`,`Station ID`"
    _stations = []

    def __init__(self, credentials: Credentials, store=True) -> None:
        self.credentials = credentials
        self.table_name = f"{credentials.project_id}.Transport.MTR"
        self.store = store
        self.embeddings = VertexAIEmbeddings(
            credentials=credentials,
            project=credentials.project_id,
            model_name="text-multilingual-embedding-002",
        )
        chroma_param = {
            "collection_name": self.chroma_db_collection,
            "embedding_function": self.embeddings,
        }
        if self.store:
            chroma_param["persist_directory"] = self.chroma_db_path
        self.vector_store = Chroma(**chroma_param)

    def load_data(self,):
        data_file = open(self.mtr_data_csv, 'r', encoding="utf-8")
        raw_data = data_file.read()
        # Replace " with none
        raw_data = raw_data.replace("\"", "")
        data_lines = str(raw_data).split("\n")
        # Read csv headers
        headers = str(data_lines[0]).split(",")
        stations = [line.split(",") for line in data_lines[1:]]
        # Format CSV to Text Document
        documents = []
        for station in stations:
            if len(station) < 2 or station[0] == "":
                continue
            station_text = []
            for i in range(len(headers)):
                station_text.append(f"{headers[i]}: {station[i]}")
            station_text = ", ".join(station_text)
            print("Adding: " + station_text + " to Chroma DB")
            documents.append(Document(page_content=station_text))
        self.vector_store.add_documents(documents=documents)

    @staticmethod
    def listdictify_query(results: RowIterator):
        return [{column.name: station[column.name] for column in results.schema
                 } for station in results]

    @property
    def stations(self) -> list[dict[str, str]]:
        docs_in_db = self.vector_store.get(include=["documents"])["documents"]
        if not docs_in_db:
            self.load_data()
            docs_in_db = self.vector_store.get(
                include=["documents"])["documents"]
        # print(docs_in_db)
        stations = [{
            doc_c.split(':')[0]: doc_c.split(':')[1] for doc_c in str(doc).split(',')
        } for (doc) in docs_in_db]
        return stations

    @staticmethod
    def prettify_station(stations: list[dict[str, str]] | dict[str, str]) -> str:
        if type(stations) is not list:
            stations = [stations]
        headers = ",".join(stations[0].keys())
        values = "\n".join(
            [",".join(str(value) for value in station.values()) for station in stations])
        return f"{headers}\n{values}"

    def get_station_from_station_id(self, station_id: int) -> dict[str, str] | None:
        filtered_stations = list(
            filter(lambda station: station['Station ID'] == station_id, self.stations))
        return filtered_stations[0] if filtered_stations else None

    def get_station_from_station_code(self, station_code: str) -> dict[str, str] | None:
        filtered_stations = list(
            filter(lambda station: station['Station Code'] == station_code, self.stations))
        return filtered_stations[0] if filtered_stations else None

    def get_station_from_station_name(self, station_name: str) -> dict[str, str] | None:
        filtered_stations = list(
            filter(lambda station: station['English Name'].lower() == station_name.lower() or station["Chinese Name"].lower() == station_name.lower(), self.stations))
        return filtered_stations[0] if filtered_stations else None

    def get_from_and_to_station_path(self, originStationId: int, destinationStationId: int) -> str:
        queryParams = f'lang=E&o={originStationId}&d={destinationStationId}'
        json_data = fetch(
            "https://www.mtr.com.hk/share/customer/jp/api/HRRoutes/?" + queryParams)
        if json_data.get("errorCode") != "0":
            return json_data.get("errorMsg")
        text = []
        text.append("Terms and Conditions:")
        text.append(json_data['tnc'])

        for route in json_data['routes']:
            text.append(f"\nRoute Option Name: {route['routeName']}")
            text.append(f"Total Time: {route['time']} minutes")
            text.append(f"Walking Time: {route['walkingTime']} minutes")
            text.append("Fares:")
            for fare in route['fares']:
                text.append(f"  {fare['fareTitle']}:")
                for category, prices in dict(fare['fareInfo']).items():
                    text.append(
                        f"    {str(category).capitalize()}: Octopus - {dict(prices).get('octopus')}, Single Journey - {dict(prices).get('sj')}")
            text.append("Path:(Sequence of Stations)")
            for path in route['path']:
                path_text = f"{path['linkType']}: Station: {self.get_station_from_station_id(int(path['ID']))['English Name']}, Time: {path['time']} minutes, {path['linkText'] if path['linkText'] else ''}"
                text.append(f"  {path_text}")

        return "\n".join(text)


if __name__ == "__main__":
    credentials = Credentials.from_service_account_file('gcp_cred-data.json')
    mtr = MTRApi(credentials=credentials)
    print(mtr.stations)
    # station = mtr.get_station_from_station_code("AWE")
    # print(mtr.prettify_station(mtr.stations))
    # start = mtr.get_station_from_station_name("Sheung Shui")
    # end = mtr.get_station_from_station_name("South Horizons")
    # print(mtr.get_from_and_to_station_path(
    #     start.get('Station ID', 1), end.get('Station ID', 1)))

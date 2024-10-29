import os
import inspect

from google.oauth2.service_account import Credentials
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from ..ExternalIo import fetch, write_file


class MTRApi():

    _stations = []

    def print_log(self, msg: str) -> None:
        if not self.verbose:
            return
        print(f'\033[41;37m[{inspect.stack()[1][3]}] ' + msg + '\x1b[0m')

    def __init__(self,
                 credentials: Credentials,
                 store=True,
                 verbose=False,
                 chroma_db_path="./chroma_db",
                 chroma_db_colection="mtr",
                 data_csv_file_path="./data/mtr_lines_and_stations.csv",
                 mtr_data_url="https://opendata.mtr.com.hk/data/mtr_lines_and_stations.csv",
                 **kwargs
                 ) -> None:
        self.verbose = verbose
        self.store = store
        self.chroma_db_path = chroma_db_path
        self.chroma_db_collection = chroma_db_colection
        self.data_csv_file_path = data_csv_file_path
        self.data_url = mtr_data_url

        self.print_log("Initializing Chroma")
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
            self.print_log("Chroma presist directory Enabled")
            chroma_param["persist_directory"] = self.chroma_db_path
        self.vector_store = Chroma(**chroma_param)
        self.print_log("Finished Initializing Chroma")
        # Verify Data
        self.print_log("Verifying Chroma db data exists")
        docs_in_db = self.vector_store.get(
            include=["documents"], limit=1)["documents"]
        if not docs_in_db:
            self.print_log("Empty Chroma db, loading data")
            self.load_data()
        self.print_log("Data Exists in Chroma DB, clear to proceed")

    def load_data(self):
        if not os.path.exists(self.data_csv_file_path) or not self.store:
            self.print_log("File path {} does not exists, fetching from url".format(
                self.data_csv_file_path))
            raw_data = fetch(self.data_url)

            if self.store:
                write_file(raw_data, self.data_csv_file_path)
        else:
            data_file = open(self.data_csv_file_path, 'r', encoding="utf-8")
            raw_data = data_file.read()

        # Replace " with none
        raw_data = raw_data.replace("\"", "")
        data_lines = str(raw_data).split("\n")

        # Read csv headers
        headers = str(data_lines[0]).split(",")
        stations = list(map(lambda l: l.split(','), data_lines[1:]))

        # Format CSV to Text Document
        documents = []
        for station in stations:
            if len(station) < 2 or station[0] == "":
                continue
            station_text = ", ".join(
                map(lambda i: f"{headers[i]}: {station[i]}", range(len(headers))))
            self.print_log(f"Adding: to Chroma DB {station_text.split(',')[2]}")
            documents.append(Document(page_content=station_text))

        self.vector_store.add_documents(documents=documents)
        self.print_log("Documents added to chroma DB")

    @staticmethod
    def format_chroma_doc_to_dict(doc: str) -> dict:
        return dict(
            map(lambda doc_c: (doc_c.split(':')[0].strip(), doc_c.split(':')[1].strip()),
                doc.split(','))
        )

    @property
    def stations(self) -> list[dict[str, str]]:
        if self._stations:
            return self._stations
        # No data in RAM
        docs_in_db = self.vector_store.get(include=["documents"])["documents"]
        if not docs_in_db:
            self.print_log('No data found in chroma db, loading data')
            self.load_data()
            docs_in_db = self.vector_store.get(
                include=["documents"])["documents"]
        # self.print_log(docs_in_db)
        self._stations = list(
            map(MTRApi.format_chroma_doc_to_dict, docs_in_db))
        return self._stations

    @staticmethod
    def prettify_station(stations: list[dict[str, str]] | dict[str, str]) -> str:
        if type(stations) is not list:
            stations = [stations]
        headers = ",".join(stations[0].keys())
        values = "\n".join(
            [",".join(str(value) for value in station.values()) for station in stations])
        return f"{headers}\n{values}"

    def get_station_from_station_id(self, station_id: int) -> dict[str, str] | None:
        self.print_log("Getting Station ID " + str(station_id))
        filtered_stations = list(
            filter(lambda station: station['Station ID'] == f"{station_id}", self.stations))
        return filtered_stations[0] if filtered_stations else None

    def get_station_from_station_code(self, station_code: str) -> dict[str, str] | None:
        self.print_log("Getting Station Code " + str(station_code))
        filtered_stations = list(
            filter(lambda station: station['Station Code'] == f"{station_code}", self.stations))
        return filtered_stations[0] if filtered_stations else None

    def get_station_from_station_name(self, station_name: str) -> list[dict[str, str]] | None:
        self.print_log("Seasrching Station Name " + str(station_name))
        if self.vector_store.get(limit=1, include=["documents"])["documents"] == []:
            self.print_log(
                "No data in Chroma DB yet. Calling .stations to inti chroma db")
            self.stations
        resault = self.vector_store.similarity_search(station_name, k=4)
        self.print_log("Found Station " + str(resault))
        return list(map(MTRApi.format_chroma_doc_to_dict, list(map(lambda d: d.page_content, resault))))

    def get_route_suggestion(self, originStationId: int, destinationStationId: int) -> str:
        queryParams = f'lang=E&o={originStationId}&d={destinationStationId}'
        json_data = fetch(
            url="https://www.mtr.com.hk/share/customer/jp/api/HRRoutes/?" + queryParams,
            log_print=self.verbose
        )
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
                path_text = "{}: Station: {}, Time: {} minutes, {}".format(
                    path['linkType'],
                    self.get_station_from_station_id(
                        path['ID'])['English Name'],
                    path['time'],
                    path['linkText'] if path['linkText'] else '',
                )
                text.append(f"  {path_text}")

        return "\n".join(text)


if __name__ == "__main__":
    credentials = Credentials.from_service_account_file('gcp_cred-ai.json')
    mtr = MTRApi(credentials=credentials, verbose=True)
    # print(mtr.stations)
    # print(mtr.prettify_station(mtr.stations))
    # print(mtr.prettify_station(mtr.get_station_from_station_name("Kowlon Bay")))
    # station = mtr.get_station_from_station_code("AWE")
    # print(mtr.prettify_station(mtr.stations))
    start = mtr.get_station_from_station_name("Sheung Shui")[0]
    end = mtr.get_station_from_station_name("South Horizons")[0]
    print(mtr.get_from_and_to_station_path(
        start.get('Station ID', 1), end.get('Station ID', 1)))

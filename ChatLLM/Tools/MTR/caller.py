import os
import inspect

import typing as t

from google.oauth2.service_account import Credentials
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from ..ExternalIo import fetch, write_file, read_file, logger


class MTRApi():

    _stations = []

    def __init__(self,
                 credentials: t.Optional[Credentials] = None,
                 store=True,
                 chroma_db_path="./chroma_db",
                 chroma_db_colection="mtr",
                 data_csv_file_path="./data/mtr_lines_and_stations.csv",
                 mtr_data_url="https://opendata.mtr.com.hk/data/mtr_lines_and_stations.csv",
                 **kwargs
                 ) -> None:
        self.store = store
        self.chroma_db_path = chroma_db_path
        self.chroma_db_collection = chroma_db_colection
        self.data_csv_file_path = data_csv_file_path
        self.data_url = mtr_data_url

        logger.debug("Initializing Chroma")
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
            logger.debug("Chroma presist directory Enabled")
            chroma_param["persist_directory"] = self.chroma_db_path
        self.vector_store = Chroma(**chroma_param)
        logger.debug("Finished Initializing Chroma")
        # Verify Data
        logger.debug("Verifying Chroma db data exists")
        docs_in_db = self.vector_store.get(
            include=["documents"], limit=1)["documents"]
        if not docs_in_db:
            logger.debug("Empty Chroma db, loading data")
            self.load_data()
        logger.debug("Data Exists in Chroma DB, clear to proceed")

    def load_data(self):
        if not os.path.exists(self.data_csv_file_path) or not self.store:
            logger.debug("File path {} does not exists, fetching from url".format(
                self.data_csv_file_path))
            raw_data = fetch(self.data_url)

            if self.store:
                write_file(str(raw_data), self.data_csv_file_path)
        else:
            raw_data = read_file(self.data_csv_file_path)

        # Replace " with none
        raw_data = str(raw_data).replace("\"", "")
        data_lines = str(raw_data).split("\n")

        # Read csv headers
        headers = str(data_lines[0]).split(",")
        stations = list(map(lambda l: l.split(','), data_lines[1:]))

        # Format CSV to Text Document
        documents = []

        logger.debug(f"Adding data to chroma db")
        for station in stations:
            if len(station) < 2 or station[0] == "":
                continue
            station_text = ", ".join(
                map(lambda i: f"{headers[i]}: {station[i]}", range(len(headers))))
            documents.append(Document(page_content=station_text))

        self.vector_store.add_documents(documents=documents)
        logger.debug("Documents added to chroma DB")

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
            logger.debug('No data found in chroma db, loading data')
            self.load_data()
            docs_in_db = self.vector_store.get(
                include=["documents"])["documents"]
        # logger.debug(docs_in_db)
        self._stations = list(
            map(MTRApi.format_chroma_doc_to_dict, docs_in_db))
        return self._stations

    @staticmethod
    def prettify_station(stations: list[dict[str, str]] | dict[str, str]) -> str:
        if type(stations) is not list:
            stations = [stations] if isinstance(stations, dict) else stations
        headers = ",".join(stations[0].keys())
        values = "\n".join(
            [",".join(str(value) for value in station.values()) for station in stations])
        return f"{headers}\n{values}"

    def get_station_from_station_id(self, station_id: int) -> dict[str, str] | None:
        logger.debug("Getting Station ID " + str(station_id))
        filtered_stations = list(
            filter(lambda station: station['Station ID'] == f"{station_id}", self.stations))
        return filtered_stations[0] if filtered_stations else None

    def get_station_from_station_code(self, station_code: str) -> dict[str, str] | None:
        logger.debug("Getting Station Code " + str(station_code))
        filtered_stations = list(
            filter(lambda station: station['Station Code'] == f"{station_code}", self.stations))
        return filtered_stations[0] if filtered_stations else None

    def get_station_from_station_name(self, station_name: str) -> list[dict[str, str]] | None:
        logger.debug("Seasrching Station Name " + str(station_name))
        if self.vector_store.get(limit=1, include=["documents"])["documents"] == []:
            logger.debug(
                "No data in Chroma DB yet. Calling .stations to inti chroma db")
            self.stations
        resault = self.vector_store.similarity_search(station_name, k=4)
        logger.debug("Found Station " + str(resault))
        return list(map(MTRApi.format_chroma_doc_to_dict, list(map(lambda d: d.page_content, resault))))

    def get_route_suggestion(self, originStationId: int, destinationStationId: int) -> str:
        queryParams = f'lang=E&o={originStationId}&d={destinationStationId}'
        json_data = fetch(url="https://www.mtr.com.hk/share/customer/jp/api/HRRoutes/?" + queryParams)
        if isinstance(json_data, dict) and json_data.get("errorCode") != "0":
            return json_data.get("errorMsg", "Unknown error")
        text = []
        text.append("Terms and Conditions:")
        if isinstance(json_data, dict) and 'tnc' in json_data:
            text.append(json_data['tnc'])

        if not isinstance(json_data, dict):
            return "No Data"
        for route in json_data.get('routes', []):
            text.append(f"\nRoute Option Name: {route['routeName']}")
            text.append(f"Total Time: {route['time']} minutes")
            text.append(f"Walking Time: {route['walkingTime']} minutes")
            text.append("Fares:")
            for fare in route['fares']:
                text.append(f"  {fare['fareTitle']}:")
                for category, prices in dict(fare['fareInfo']).items():
                    text.append("    {}: Octopus - {}, Single Journey - {}".format(
                        str(category).capitalize(),
                        dict(prices).get('octopus'),
                        dict(prices).get('sj'),
                    ))

            text.append("Path:(Sequence of Stations)")
            for path in route['path']:
                path_text = "{}: Station: {}, Time: {} minutes, {}".format(
                    path['linkType'],
                    (self.get_station_from_station_id(path.get("ID") or -1) or {}).get('English Name', 'Unknown Station'),
                    path['time'],
                    path['linkText'] if path['linkText'] else '',
                )
                text.append(f"  {path_text}")

        return "\n".join(text)

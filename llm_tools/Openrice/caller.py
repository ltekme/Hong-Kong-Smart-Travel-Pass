import os
import inspect

from google.oauth2.service_account import Credentials
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from ..ExternalIo import fetch, write_json_file, read_json_file


def divide_chunks(data, chunk_size):
    """Yield successive n-sized chunks from data."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


class OpenriceBase():

    lang_dict_options: dict = ["en", "tc", "sc"]

    def __init__(self, verbose: bool):
        self.verbose = verbose

    def logger(self, msg: str):
        if self.verbose:
            print(
                f'\033[43;30m[openrice][{inspect.stack()[1][3]}] ' + msg + '\x1b[0m')


class FilterBase(OpenriceBase):

    _raw_data = None
    _data = None
    _FILTER_RAW_DATA_URL: str = "https://www.openrice.com/api/v2/metadata/region/all?uiLang=zh&uiCity=hongkong"
    _METADATA_RAW_DATA_URL: str = "https://www.openrice.com/api/v2/metadata/country/all"

    def __init__(self,
                 searchKey: str,
                 searchKeyParentKey: list[str],
                 credentials: Credentials,
                 store_data: bool = True,
                 verbose: bool = False,
                 data_base_path: str = "./data",
                 chroma_db_path: str = "./chroma_db",
                 chroma_db_collection_prefix: str = "shitrice",
                 metadata_url=False,
                 data_url=None,
                 **kwargs,
                 ):
        super().__init__(verbose)
        self.searchKey = searchKey
        self.store_data = store_data

        self.data_url = data_url or self._FILTER_RAW_DATA_URL if not metadata_url else self._METADATA_RAW_DATA_URL
        if not metadata_url:
            self.raw_data_path = os.path.join(
                data_base_path, "openrice_raw.json")
        else:
            self.raw_data_path = os.path.join(
                data_base_path, "openrice_metadata_raw.json")

        self.data_path = os.path.join(
            data_base_path, f"openrice_{searchKey}.json")

        self.logger(f"initializing {searchKey} filter")
        embeddings = VertexAIEmbeddings(
            credentials=credentials,
            project=credentials.project_id,
            model_name="text-multilingual-embedding-002",
        )
        chroma_param = {
            "collection_name": chroma_db_collection_prefix,
            "embedding_function": embeddings,
        }

        if self.store_data:
            self.logger("chroma presist directory enabled")
            chroma_param["persist_directory"] = chroma_db_path

        self.logger("setting up chromadb")
        self.vector_store = Chroma(**chroma_param)

        self.logger(f"setting up {searchKey} filter data")
        if self.store_data and os.path.exists(self.data_path):
            self.logger(f"getting {searchKey} filter from file")
            self._data = read_json_file(self.data_path)

        self.logger(
            f"{searchKey} filter data not in file or file store not enabled, parsing from raw data")

        # get the items from list of dict keys
        searchKeyMap = self.raw_data
        for layer in searchKeyParentKey:
            searchKeyMap = searchKeyMap[layer]

        if not self._data:
            self._data = list(map(lambda d: {
                self.searchKey: d["searchKey"].split("=")[1],
                **{f"name{l.upper()}": d["nameLangDict"][l] for l in self.lang_dict_options},
            }, searchKeyMap))
            if self.store_data:
                write_json_file(self._data, self.data_path)

        self.init_chroma(self._data)

        self.logger(f"filter {searchKey} loaded")

    @property
    def raw_data(self):
        self.logger("getting raw data from cache")
        if self._raw_data:
            self.logger("raw data exist in cache, returning")
            return self._raw_data

        self.logger("raw data not exist in cache")
        if self.store_data and os.path.exists(self.raw_data_path):
            self.logger("getting raw data from file")
            self._raw_data = read_json_file(self.raw_data_path)
            if self._raw_data:
                self.logger("got raw data from file, returning")
                return self._raw_data

        self.logger(
            "raw data not in file or file store not enabled, fetching from api")
        raw_data = fetch(self.data_url)
        if self.store_data:
            self.logger("storage enabled, writing raw data to file")
            write_json_file(raw_data, self.raw_data_path)
        self.logger("got raw data from API, returning")
        return raw_data

    def init_chroma(self, data_expected: list[dict]):
        self.logger(f"attempt to get {self.searchKey} data from chroma")
        coll = self.vector_store.get(
            where={"openrice_searchKey": self.searchKey},
            include=["metadatas"],
        )
        collection_len = len(coll["ids"])
        data_expected_len = len(data_expected)
        if collection_len != data_expected_len:
            self.logger(
                f"{self.searchKey} data count mismatch ({collection_len=} {data_expected_len=}), cleaning up chroma db")
            if collection_len > 0:
                self.vector_store._collection.delete(coll["ids"])
            else:
                self.logger(
                    f"empty collection for {self.searchKey} nothing to delete")

            self.logger("adding documents to chroma db")
            self.vector_store.add_documents(list(map(lambda item: Document(
                ', '.join(list(map(
                    lambda l: f"{str(l)}: {item[l]}",
                    dict(item).keys(),
                ))),
                metadata={
                    "openrice_searchKey": self.searchKey,
                    "source": self.data_url,
                },
            ), data_expected)))

        self.logger(f"finishing initializing chroma db for {self.searchKey}")


class LandmarkFilter(FilterBase):

    description = "Search for restaurants near a specific landmark. Find places to eat near popular attractions like Ocean Park or Hong Kong Disneyland, shopping malls like IFC or Times Square, or transport hubs like Central Station."
    tool_description = "Provide a JSON array of landmark IDs (e.g., [9319, 7, 18]). Leave blank or provide an empty array [] for all landmarks." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "landmarkId"
        kwargs["searchKeyParentKey"] = ["landmarks"]
        super().__init__(**kwargs)

    @property
    def all(self) -> list:
        return self._data


class DistrictFilter(FilterBase):

    description = "Narrow your search by geographical area. Find restaurants on Hong Kong Island (Central, Causeway Bay), in Kowloon (Tsim Sha Tsui, Mong Kok), the New Territories (Tsuen Wan, Sha Tin), or the Outlying Islands (Lantau, Cheung Chau)."
    tool_description = "Provide a JSON array of district IDs (e.g., [1999, 2999, 3999]). Leave blank or provide an empty array [] for all districts. " + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "districtId"
        kwargs["searchKeyParentKey"] = ["districts"]
        super().__init__(**kwargs)

    @property
    def all(self) -> list:
        return self._data


class CuisineFilter(FilterBase):

    description = "This filter helps you narrow down restaurants based on their culinary style. Options include broad categories like Western, Japanese, and International, as well as more specific regional cuisines like Hong Kong Style, Sichuan, and Vietnamese."
    tool_description = "Provide a JSON array of cuisine IDs (e.g., [4000, 1004, 2009]). Leave blank or provide an empty array [] for all cuisines. " + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "cuisineId"
        kwargs["searchKeyParentKey"] = ["categories", "cuisine"]
        super().__init__(**kwargs)

    @property
    def all(self) -> list:
        return self._data


class DishFilter(FilterBase):

    description = """This filter lets you find restaurants serving particular dishes or types of food. Examples include Fine Dining experiences, All-you-can-eat buffets, Omakase menus, Hot Pot, Sushi/Sashimi, Desserts, and more specific items like Ramen, Korean Fried Chicken, or Snake Soup. This filter focuses on the format or kind of food offered."""
    tool_description = "Provide a JSON array of dish IDs (e.g., [1200, 1076, 1001]). Leave blank or provide an empty array [] for all dishes." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "dishId"
        kwargs["searchKeyParentKey"] = ["categories", "dish"]
        super().__init__(**kwargs)

    @property
    def all(self) -> list:
        return self._data


class ThemeFilter(FilterBase):

    description = """This filter categorizes restaurants by the dining experience they offer. For example, "Romantic Dining", "Business Dining", "Family Style Dining", "Private Party", and "Group Dining" help users find places suitable for specific occasions or social settings. This filter describes the overall atmosphere or purpose of a dining experience."""
    tool_description = "Provide a JSON array of theme IDs (e.g., [8, 2, 1]). Leave blank or provide an empty array [] for all themes." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "themeId"
        kwargs["searchKeyParentKey"] = ["categories", "theme"]
        super().__init__(**kwargs)

    @property
    def all(self) -> list:
        return self._data


class AmenityFilter(FilterBase):

    description = """This filter helps you find restaurants with specific features or services. Options like "Steak House", "Dim Sum Restaurant", "Salt & Sugar Reduction Restaurant", "Pet Friendly", and "Food Wise Eateries" allow users to select based on the restaurant's environment, target audience, or health-conscious options. It focuses on the restaurant's attributes or services."""
    tool_description = "Provide a JSON array of amenity IDs (e.g., [1093, 1003, 1001]). Leave blank or provide an empty array [] for all amenities." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "amenityId"
        kwargs["searchKeyParentKey"] = ["categories", "amenity"]
        super().__init__(**kwargs)

    @property
    def all(self) -> list:
        return self._data


class PriceRangeFilter(FilterBase):

    description = "The IDs correspond to the following ranges: 1 (Below $50), 2 ($51-100), 3 ($101-200), 4 ($201-400), 5 ($401-800), and 6 (Above $801)."
    tool_description = "Provide a JSON array of price range IDs (e.g., [1, 2, 3]) to filter restaurants by price. Leave blank or provide an empty array [] for all price ranges." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "priceRangeId"
        kwargs["searchKeyParentKey"] = ["regions", "0", "priceRanges"]
        kwargs["metadata_url"] = True
        super().__init__(**kwargs)

    @property
    def all(self) -> list:
        return self._data


if __name__ == "__main__":
    # cannot directory run, but can be imported to test
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)
    kwargs = {"verbose": True, "credentials": credentials}
    print(LandmarkFilter(**kwargs).all[0])
    print(DistrictFilter(**kwargs).all[0])
    print(CuisineFilter(**kwargs).all[0])
    print(DishFilter(**kwargs).all[0])
    print(ThemeFilter(**kwargs).all[0])
    print(AmenityFilter(**kwargs).all[0])
    print(PriceRangeFilter(**kwargs).all[0])

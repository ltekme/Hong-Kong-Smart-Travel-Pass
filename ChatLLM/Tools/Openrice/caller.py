import os
import inspect
import typing as t
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

    lang_dict_options: list = ["en", "tc", "sc"]

    def __init__(self, verbose: bool):
        self.verbose = verbose

    def logger(self, msg: str):
        if self.verbose:
            print(
                f'\033[43;30m[openrice][{inspect.stack()[1][3]}] ' + msg + '\x1b[0m')


class FilterBase(OpenriceBase):

    _raw_data = None
    _data = None
    _FILTER_RAW_DATA_URL: str = "https://www.openrice.com/api/v2/metadata/region/all?uiLang=en&uiCity=hongkong"
    _METADATA_RAW_DATA_URL: str = "https://www.openrice.com/api/v2/metadata/country/all"

    def __init__(self,
                 credentials: Credentials,
                 store_data: bool = True,
                 verbose: bool = False,
                 searchKey: str = "",
                 searchKeyParentKey: list[str] = [],
                 data_base_path: str = "./data",
                 chroma_db_path: str = "./chroma_db",
                 chroma_db_collection_prefix: str = "shitrice",
                 metadata_url=False,  # weather to use metadata url or filter url
                 data_url=None,  # custom data url, data schema must match api
                 ):
        super().__init__(verbose)
        self.searchKey = searchKey
        self.store_data = store_data

        # chroma setup
        self.logger(f"initializing chroma db filter for {searchKey}")
        # when only doing where doc search, no embedding func is needed
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

        # case for non specific filter, dont inti data
        if self.searchKey is None:
            self.logger(
                "Non specific filter is search key is specificed, exiting data init, chroma db may containes incomplete or incorrect data"
            )
            return

        # split between data in metadata api url or filter data url
        self.data_url = data_url or self._FILTER_RAW_DATA_URL if not metadata_url else self._METADATA_RAW_DATA_URL
        if not metadata_url:
            self.raw_data_path = os.path.join(
                data_base_path, "openrice_raw.json")
        else:
            self.raw_data_path = os.path.join(
                data_base_path, "openrice_metadata_raw.json")

        self.data_path = os.path.join(
            data_base_path, f"openrice_{searchKey}.json")

        # check data file exists and appempt load
        self.logger(f"setting up {searchKey} filter data")
        if self.store_data and os.path.exists(self.data_path):
            self.logger(f"getting {searchKey} filter from file")
            self._data = read_json_file(self.data_path)

        # check for no data in file
        if not self._data:
            self.logger(
                f"{searchKey} filter data not in file or file store not enabled, parsing from raw data")

            # get the items from list of dict keys
            searchKeyMap = self.raw_data
            for layer in searchKeyParentKey:
                if isinstance(searchKeyMap, dict):
                    searchKeyMap = searchKeyMap[layer]
                else:
                    raise TypeError(f"Expected a dictionary for raw data but got {type(searchKeyMap)}")

            # parse to dict
            self._data = list(map(lambda d: {
                self.searchKey: d["searchKey"].split("=")[1] if isinstance(d, dict) else " ",  # type: ignore
                **{f"name{l.upper()}": d["nameLangDict"][l] for l in self.lang_dict_options},  # type: ignore
            }, searchKeyMap))

            # store data to file if enabled
            if self.store_data:
                write_json_file(self._data, self.data_path)

        if isinstance(self._data, list) and all(isinstance(i, dict) for i in self._data):
            self.init_chroma_data(self._data)
        else:
            raise TypeError("Expected self._data to be a list of dictionaries")

        self.logger(f"filter {searchKey} data loaded")

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
            # self.logger(f"Got data from file: {self._raw_data}")
            if self._raw_data:
                self.logger("got raw data from file, returning")
                return self._raw_data

        self.logger(
            "raw data not in file or file store not enabled, fetching from api")
        raw_data = fetch(self.data_url)
        if self.store_data:
            self.logger("storage enabled, writing raw data to file")
            if isinstance(raw_data, (dict, list)):
                write_json_file(raw_data, self.raw_data_path)
            else:
                self.logger(f"Error, Got {type(raw_data)=},{raw_data=}")
                raise TypeError("Expected raw_data to be a dictionary or list")
        self.logger("got raw data from API, returning")
        return raw_data

    def init_chroma_data(self, data_expected: list[dict]):
        self.logger(f"attempt to get {self.searchKey} data from chroma")
        coll = self.vector_store.get(
            where={"$and": [
                {"openrice_searchKey": self.searchKey},
                {"type": "openrice_searchKey_filters"},
            ]},
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
                    lambda l: f"\"{str(l)}\": \"{item[l]}\"",
                    dict(item).keys(),
                ))),
                metadata={
                    "openrice_searchKey": self.searchKey,
                    "source": self.data_url,
                    "type": "openrice_searchKey_filters",
                },
            ), data_expected)))

        self.logger(f"finishing initializing chroma db for {self.searchKey}")

    @property
    def all(self) -> list:
        if isinstance(self._data, list):
            return self._data
        return []

    def search(self, keyword: str) -> list[str]:
        search_param = {
            "query": keyword,
            "k": 5,
            "filter": {
                "type": "openrice_searchKey_filters"
            }
        }
        if self.searchKey is not None:
            search_param["filter"]["openrice_searchKey"] = self.searchKey

        return list(map(
            lambda doc: doc.page_content,
            self.vector_store.similarity_search(**search_param)
        ))

    def by_id(self, id: int) -> dict | None:
        if not self.searchKey:
            raise NotImplementedError(
                "This methoad cannot be called on instence without searchKey")
        resault = list(filter(
            # is is compairing string because my dumb fuck decided to get the id from search key string so everything is compatable.
            lambda flt: flt[self.searchKey] == f"{id}",
            self._data if isinstance(self._data, list) else []
        ))
        if resault != []:
            return resault[0]
        return None

    def get_api_filter_search_key(self, id: int) -> str:
        self.logger(f"getting {id=} on {self.searchKey}")
        if self.by_id(id) != None:
            self.logger(f"found {id=} on {self.searchKey}")
            return f"{self.searchKey}={id}"
        self.logger(f"{id=} not found on {self.searchKey}")
        return ""


class LandmarkFilter(FilterBase):

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "landmarkId"
        kwargs["searchKeyParentKey"] = ["landmarks"]
        super().__init__(**kwargs)


class DistrictFilter(FilterBase):

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "districtId"
        kwargs["searchKeyParentKey"] = ["districts"]
        super().__init__(**kwargs)


class CuisineFilter(FilterBase):

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "cuisineId"
        kwargs["searchKeyParentKey"] = ["categories", "cuisine"]
        super().__init__(**kwargs)


class DishFilter(FilterBase):

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "dishId"
        kwargs["searchKeyParentKey"] = ["categories", "dish"]
        super().__init__(**kwargs)


class ThemeFilter(FilterBase):

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "themeId"
        kwargs["searchKeyParentKey"] = ["categories", "theme"]
        super().__init__(**kwargs)


class AmenityFilter(FilterBase):

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "amenityId"
        kwargs["searchKeyParentKey"] = ["categories", "amenity"]
        super().__init__(**kwargs)


class PriceRangeFilter(FilterBase):

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "priceRangeId"
        kwargs["searchKeyParentKey"] = ["regions", "0", "priceRanges"]
        kwargs["metadata_url"] = True
        super().__init__(**kwargs)


class Filters(FilterBase):
    def __init__(self, **kwargs):
        kwargs["searchKey"] = None
        super().__init__(**kwargs)
        self.landmark = LandmarkFilter(**kwargs)
        self.district = DistrictFilter(**kwargs)
        self.cuisine = CuisineFilter(**kwargs)
        self.dish = DishFilter(**kwargs)
        self.theme = ThemeFilter(**kwargs)
        self.amenity = AmenityFilter(**kwargs)
        self.priceRange = PriceRangeFilter(**kwargs)


class RestaurantSearchApi(OpenriceBase):
    _SEARCH_BASE_API_URL: str = "https://www.openrice.com/api/v2/search?uiCity=hongkong&regionId=0&pageToken=CONST_DUMMY_TOKEN"

    def __init__(self,
                 credentials: Credentials,
                 verbose: bool = False,
                 **kwargs):
        kwargs["credentials"] = credentials
        kwargs["verbose"] = verbose
        super().__init__(verbose)
        self.filters = Filters(**kwargs)

    def format_opening_hours(self, data):
        self.logger(f"processing opening hours on {data[0]['poiId']=}")
        # Dictionary to hold the strings for each day of the week and special days
        days = {
            "Monday": [],
            "Tuesday": [],
            "Wednesday": [],
            "Thursday": [],
            "Friday": [],
            "Saturday": [],
            "Sunday": [],
            "Holiday": [],
            "HolidayEve": []
        }
        # Mapping of dayOfWeek to day names
        day_map = {
            1: "Sunday",
            2: "Monday",
            3: "Tuesday",
            4: "Wednesday",
            5: "Thursday",
            6: "Friday",
            7: "Saturday",
        }

        # Iterate through the list of POI hours
        for entry in data:
            day_of_week = entry["dayOfWeek"]
            if entry["isHoliday"]:
                days["Holiday"].append(
                    f"Holiday: {entry['period1Start']} - {entry['period1End']}")
                if "period2Start" in entry:
                    days["Holiday"].append(
                        f"Holiday: {entry['period2Start']} - {entry['period2End']}")

            elif entry["isHolidayEve"]:
                days["HolidayEve"].append(
                    f"Holiday Eve: {entry['period1Start']} - {entry['period1End']}")
                if "period2Start" in entry:
                    days["HolidayEve"].append(
                        f"Holiday Eve: {entry['period2Start']} - {entry['period2End']}")
            else:
                day_name = day_map.get(day_of_week, "Unknown")
                period1 = f"{entry['period1Start']} - {entry['period1End']}" if "period1Start" in entry else ""
                period2 = f"{entry['period2Start']} - {entry['period2End']}" if "period2Start" in entry else ""
                periods = f"{period1} {period2}".strip()
                if day_name == "Unknown":
                    pass
                else:
                    days[day_name].append(f"{day_name}: {periods}")

        # Convert the dictionary to a list of strings
        result = []
        for day, entries in days.items():
            result.append(f"{day}:")
            result.extend(entries)
        return result

    def format_raw_restaurant_data(self, raw_data: dict) -> dict:
        self.logger(f"parsing poiId:{raw_data['poiId']}")
        return {
            "name": raw_data.get('name'),
            "openSince": raw_data.get("openSince"),
            "address": raw_data.get('address'),
            "geolocation": (raw_data.get("mapLatitude"), raw_data.get("mapLongitude")),
            "phones": {
                "remarks": raw_data.get("phoneRemarks"),
                "numbers": raw_data.get("phones"),
            },
            "priceRangeId": self.filters.priceRange.by_id(raw_data.get("priceRangeId", -1)),
            "shortUrl": raw_data.get("shortenUrl"),
            "district": raw_data.get("district", {}).get("name"),
            "categories": list(map(lambda n: n.get("name"), raw_data.get("categories", []))),
            "bookingOffers": list(map(lambda o: o.get("title"), raw_data.get("bookingOffers", []))),
            "altCallName": raw_data.get("latestCallName"),
            "thumbnail": raw_data.get("doorPhoto", {}).get("url"),
            "openingHours": self.format_opening_hours(raw_data.get("poiHours"))
        }

    def to_beautify_string(self, data: dict) -> str:
        text_item = ""
        for key, value in data.items():
            if isinstance(value, dict):
                text_item += f"{key.capitalize()}:\n"
                for sub_key, sub_value in value.items():
                    text_item += f"    {sub_key.capitalize()}: {sub_value}\n"
            elif isinstance(value, list):
                text_item += f"{key.capitalize()}: {', '.join(value)}\n"
            else:
                text_item += f"{key.capitalize()}: {value}\n"
        return text_item

    def search(self,
               landmarkIds: list[int] = [],
               districtIds: list[int] = [],
               cuisineIds: list[int] = [],
               dishIds: list[int] = [],
               themeIds: list[int] = [],
               amenityIds: list[int] = [],
               priceRangeIds: list[int] = [],
               keywords: str = "",
               count: int = 3
               ) -> list[dict]:

        filterSearchKeys = []
        # landmark
        if type(landmarkIds) == int:
            landmarkIds = [landmarkIds]
        for id in landmarkIds:
            self.logger(f"finding {landmarkIds=} to search")
            searchKey = self.filters.landmark.get_api_filter_search_key(id)
            if searchKey:
                self.logger(f"adding {searchKey=} to search key")
                filterSearchKeys.append(searchKey)
        # district]
        if type(districtIds) == int:
            districtIds = [districtIds]
        for id in districtIds:
            self.logger(f"finding {districtIds=} to search")
            searchKey = self.filters.district.get_api_filter_search_key(id)
            if searchKey:
                filterSearchKeys.append(searchKey)
        # cuisine
        if type(cuisineIds) == int:
            cuisineIds = [cuisineIds]
        for id in cuisineIds:
            self.logger(f"finding {cuisineIds=} to search")
            searchKey = self.filters.cuisine.get_api_filter_search_key(id)
            if searchKey:
                self.logger(f"adding {searchKey=} to search key")
                filterSearchKeys.append(searchKey)
        # dish
        if type(dishIds) == int:
            dishIds = [dishIds]
        for id in dishIds:
            self.logger(f"finding {dishIds=} to search")
            searchKey = self.filters.dish.get_api_filter_search_key(id)
            if searchKey:
                self.logger(f"adding {searchKey=} to search key")
                filterSearchKeys.append(searchKey)
        # theme
        if type(themeIds) == int:
            themeIds = [themeIds]
        for id in themeIds:
            self.logger(f"finding {themeIds=} to search")
            searchKey = self.filters.theme.get_api_filter_search_key(id)
            if searchKey:
                self.logger(f"adding {searchKey=} to search key")
                filterSearchKeys.append(searchKey)
        # amenity
        if type(amenityIds) == int:
            amenityIds = [amenityIds]
        for id in amenityIds:
            self.logger(f"finding {amenityIds=} to search")
            searchKey = self.filters.amenity.get_api_filter_search_key(id)
            if searchKey:
                self.logger(f"adding {searchKey=} to search key")
                filterSearchKeys.append(searchKey)
        # price range
        if type(priceRangeIds) == int:
            priceRangeIds = [priceRangeIds]
        for id in priceRangeIds:
            self.logger(f"finding {priceRangeIds=} to search")
            searchKey = self.filters.priceRange.get_api_filter_search_key(id)
            if searchKey:
                self.logger(f"adding {searchKey=} to search key")
                filterSearchKeys.append(searchKey)

        searchParams = "&".join(filterSearchKeys)
        searchUrl = self._SEARCH_BASE_API_URL + "&" + searchParams + \
            f"&startAt=0&&rows={count}&keyword={keywords}&uiLang=en"

        resault = fetch(searchUrl)
        if isinstance(resault, dict) and resault.get('success') == False:
            self.logger(f'Error: from API\n{resault}')
            return []

        if isinstance(resault, dict) and "paginationResult" in resault and "results" in resault["paginationResult"]:
            return list(map(
                self.format_raw_restaurant_data,
                resault["paginationResult"]["results"]
            ))
        else:
            self.logger(f'Unexpected API response format: {resault}')
            return []


if __name__ == "__main__":
    # cannot directory run, due to relative import
    # but can be imported to test
    credentials_path = os.getenv(
        "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
    credentials = Credentials.from_service_account_file(credentials_path)

    kwargs = {
        "verbose": True,
        "credentials": credentials
    }
    filters = Filters(**kwargs)
    resault = filters.search("kowloon bay")
    print("\n".join(resault))

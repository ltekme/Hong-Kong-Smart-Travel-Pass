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
                 credentials: Credentials,
                 store_data: bool = True,
                 verbose: bool = False,
                 searchKey: str = None,
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
                searchKeyMap = searchKeyMap[layer]

            # parse to dict
            self._data = list(map(lambda d: {
                self.searchKey: d["searchKey"].split("=")[1],
                **{f"name{l.upper()}": d["nameLangDict"][l] for l in self.lang_dict_options},
            }, searchKeyMap))

            # store data to file if enabled
            if self.store_data:
                write_json_file(self._data, self.data_path)

        self.init_chroma_data(self._data)

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
        return self._data

    def search(self, keyword: str) -> list[Document]:
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
            self._data
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

    description = "Search for restaurants near a specific landmark. Find places to eat near popular attractions like Ocean Park or Hong Kong Disneyland, shopping malls like IFC or Times Square, or transport hubs like Central Station."
    tool_description = "Provide a JSON array of landmark IDs (e.g., [9319, 7, 18]). Leave blank or provide an empty array [] for all landmarks." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "landmarkId"
        kwargs["searchKeyParentKey"] = ["landmarks"]
        super().__init__(**kwargs)


class DistrictFilter(FilterBase):

    description = "Narrow your search by geographical area. Find restaurants on Hong Kong Island (Central, Causeway Bay), in Kowloon (Tsim Sha Tsui, Mong Kok), the New Territories (Tsuen Wan, Sha Tin), or the Outlying Islands (Lantau, Cheung Chau)."
    tool_description = "Provide a JSON array of district IDs (e.g., [1999, 2999, 3999]). Leave blank or provide an empty array [] for all districts. " + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "districtId"
        kwargs["searchKeyParentKey"] = ["districts"]
        super().__init__(**kwargs)


class CuisineFilter(FilterBase):

    description = "This filter helps you narrow down restaurants based on their culinary style. Options include broad categories like Western, Japanese, and International, as well as more specific regional cuisines like Hong Kong Style, Sichuan, and Vietnamese."
    tool_description = "Provide a JSON array of cuisine IDs (e.g., [4000, 1004, 2009]). Leave blank or provide an empty array [] for all cuisines. " + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "cuisineId"
        kwargs["searchKeyParentKey"] = ["categories", "cuisine"]
        super().__init__(**kwargs)


class DishFilter(FilterBase):

    description = """This filter lets you find restaurants serving particular dishes or types of food. Examples include Fine Dining experiences, All-you-can-eat buffets, Omakase menus, Hot Pot, Sushi/Sashimi, Desserts, and more specific items like Ramen, Korean Fried Chicken, or Snake Soup. This filter focuses on the format or kind of food offered."""
    tool_description = "Provide a JSON array of dish IDs (e.g., [1200, 1076, 1001]). Leave blank or provide an empty array [] for all dishes." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "dishId"
        kwargs["searchKeyParentKey"] = ["categories", "dish"]
        super().__init__(**kwargs)


class ThemeFilter(FilterBase):

    description = """This filter categorizes restaurants by the dining experience they offer. For example, "Romantic Dining", "Business Dining", "Family Style Dining", "Private Party", and "Group Dining" help users find places suitable for specific occasions or social settings. This filter describes the overall atmosphere or purpose of a dining experience."""
    tool_description = "Provide a JSON array of theme IDs (e.g., [8, 2, 1]). Leave blank or provide an empty array [] for all themes." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "themeId"
        kwargs["searchKeyParentKey"] = ["categories", "theme"]
        super().__init__(**kwargs)


class AmenityFilter(FilterBase):

    description = """This filter helps you find restaurants with specific features or services. Options like "Steak House", "Dim Sum Restaurant", "Salt & Sugar Reduction Restaurant", "Pet Friendly", and "Food Wise Eateries" allow users to select based on the restaurant's environment, target audience, or health-conscious options. It focuses on the restaurant's attributes or services."""
    tool_description = "Provide a JSON array of amenity IDs (e.g., [1093, 1003, 1001]). Leave blank or provide an empty array [] for all amenities." + description

    def __init__(self, **kwargs):
        kwargs["searchKey"] = "amenityId"
        kwargs["searchKeyParentKey"] = ["categories", "amenity"]
        super().__init__(**kwargs)


class PriceRangeFilter(FilterBase):

    description = "The IDs correspond to the following ranges: 1 (Below $50), 2 ($51-100), 3 ($101-200), 4 ($201-400), 5 ($401-800), and 6 (Above $801)."
    tool_description = "Provide a JSON array of price range IDs (e.g., [1, 2, 3]) to filter restaurants by price. Leave blank or provide an empty array [] for all price ranges." + description

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
                period1 = f"{entry['period1Start']} - {entry['period1End']}"
                period2 = f"{entry['period2Start']} - {entry['period2End']}" if "period2Start" in entry else ""
                periods = f"{period1} {period2}".strip()
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
            "priceRangeId": self.filters.priceRange.by_id(raw_data.get("priceRangeId")),
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
               keywords: str = None,
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
        if resault.get('success') == False:
            self.logger('Error: from API\n', resault)
            return []

        return list(map(
            self.format_raw_restaurant_data,
            resault["paginationResult"]["results"]
        ))


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

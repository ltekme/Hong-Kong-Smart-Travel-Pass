import os
import json
import requests
from typing import Tuple


def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)


class OpenriceApi(object):

    SEARCH_BASE_API_URL: str = "https://www.openrice.com/api/v2/search?uiLang=zh&uiCity=hongkong&regionId=0&pageToken=CONST_DUMMY_TOKEN"
    DISTRICT_DATA_URL: str = "https://www.openrice.com/api/v2/metadata/region/all?uiLang=zh&uiCity=hongkong"
    PRICE_RANGE_DATA_URL: str = "https://www.openrice.com/api/v2/metadata/country/all"

    REQUEST_HEADERS: dict = {
        "accept": "*/*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "accept-language": "en,en-US;q=0.9,en-GB;q=0.8,en-HK;q=0.7,zh-HK;q=0.6,zh;q=0.5",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

    lang_dict_options = ["tc", "en", "sc"]

    base_data_path = "./openrice_data/"
    raw_price_range_data_path: str = base_data_path + "openrice_priceRange_raw.json"
    price_range_data_path: str = base_data_path + "openrice_priceRange.json"
    raw_district_data_path: str = base_data_path + "openrice_district_raw.json"
    district_data_path: str = base_data_path + "openrice_district.json"

    store_data: bool = True

    def write_data(self, data, path, force=False):
        if os.path.exists(path) and not force:
            print(f"Data already exists at {path}. Skipping write.")
            return
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    def fetch(self, url, params: dict = {}):
        response = requests.request(
            method=params.get("method", "GET"),
            url=url,
            headers=params.get("headers", self.REQUEST_HEADERS),
            data=params.get("body", None),
        )
        return json.loads(response.content)

    def fetch_price_range_data(self) -> Tuple[list, list]:
        # Return (raw, processed) pricerange data
        raw_price_range_data = self.fetch(self.PRICE_RANGE_DATA_URL)
        price_range_data = [{
            "nameId": data["nameLangDict"]["en"],
            "rangeId": f"from-{data['rangeStart']}-to-{data['rangeEnd']}",
            "nameLangDict": {
                "tc": data['nameLangDict']['tc'],
                "en": data['nameLangDict']['en'],
                "sc": data['nameLangDict']['sc'],
            },
        } for data in raw_price_range_data["regions"]['0']['priceRanges']]
        return (raw_price_range_data, price_range_data)

    def fetch_district_data(self) -> Tuple[list, list]:
        # Return (raw, processed) district data
        raw_district_data = self.fetch(self.DISTRICT_DATA_URL)
        district_data = [{
            "nameId": data["nameLangDict"]["en"],
            "districtId": data["districtId"],
            "nameLangDict": {
                "tc": data['nameLangDict']['tc'],
                "en": data['nameLangDict']['en'],
                "sc": data['nameLangDict']['sc'],
            },
        } for data in raw_district_data["districts"]]
        return (raw_district_data, district_data)

    def get_price_range_data(self, force=False):
        if not self.store_data:
            return self.fetch_price_range_data()[1]
        if not os.path.exists(self.price_range_data_path) or force:
            raw, processed = self.fetch_price_range_data()
            if self.store_data:
                self.write_data(raw, self.raw_price_range_data_path)
                self.write_data(processed, self.price_range_data_path)
            return processed
        with open(self.price_range_data_path, "r") as f:
            return json.load(f)

    def get_district_data(self, force=False):
        if not self.store_data:
            return self.fetch_district_data()[1]
        if not os.path.exists(self.district_data_path) or force:
            raw, processed = self.fetch_district_data()
            if self.store_data:
                self.write_data(raw, self.raw_district_data_path)
                self.write_data(processed, self.district_data_path)
            return processed
        with open(self.district_data_path, "r") as f:
            return json.load(f)

    def convert_loc_to_google_map_url(self, lat, lng):
        # https://www.google.com/maps/place/22.2814411,114.1564406
        return f"https://www.google.com/maps/place/{lat},{lng}"

    def get_price_range_text_from_id(self, price_range_id, lang="tc"):
        price_range_data = self.get_price_range_data()
        for price_range in price_range_data:
            if price_range["rangeId"] == price_range_id:
                return price_range["nameLangDict"][lang]
        return None

    def get_district_text_from_id(self, district_id, lang="tc"):
        district_data = self.get_district_data()
        for district in district_data:
            if district["districtId"] == district_id:
                return district["nameLangDict"][lang]
        return None

    def get_district_id_from_text(self, district_text, lang="tc"):
        district_data = self.get_district_data()
        for district in district_data:
            if district["nameLangDict"][lang] == district_text:
                return district["districtId"]
        return None

    def search_restaurants(self, params):
        # params: {
        #     "keyword": restaurant keyword,
        #     "start": strating pagination index -> 0,
        #     "count": number of resaults -> 3,
        #     "district": district as text,
        #     "district_lang": district language -> "tc",
        #     "lang": language in lang_dict_options-> "tc",
        # }
        if "keyword" not in params and "district" not in params:
            return None

        params["lang"] = params.get("lang", "tc")
        if params["lang"] not in self.lang_dict_options:
            raise ValueError(
                f"Language option not supported. Options: {self.lang_dict_options}")

        search_params = ""
        search_params += f"&startAt={params['start']
                                     }" if "start" in params else "&startAt=0"
        search_params += f"&rows={params['count']
                                  }" if "count" in params else "&rows=3"
        search_params += f"&whatwhere={params['keyword']
                                       }" if "keyword" in params else ""

        if "district" in params:
            if "district_lang" not in params:
                params["district_lang"] = "tc"
            district_id = self.get_district_id_from_text(
                params["district"], params["district_lang"])
            if district_id is not None:
                search_params += f"&districtId={district_id}"

        search_data = self.fetch(self.SEARCH_BASE_API_URL + search_params)

        return [{
            "name": raw_data["name"],
            "faviconUrl": raw_data["doorPhoto"]["url"],
            "address": raw_data["address"],
            "loction": {
                "latitude": raw_data["mapLatitude"],
                "longitude": raw_data["mapLongitude"],
            },
            "priceRange": {
                "text": self.get_price_range_text_from_id(raw_data["priceRangeId"], params["lang"]),
                "id": raw_data["priceRangeId"],
            },
            "district": {
                "text": self.get_district_text_from_id(raw_data["district"]["districtId"], params["lang"]),
                "id": raw_data["district"]["districtId"],
            },
            "contectInfo": {
                "openRiceShortUrl": raw_data["shortenUrl"],
                "phones": raw_data["phones"],
            },
        }for raw_data in search_data["paginationResult"]["results"]]

    def __init__(self,
                 base_data_path="./openrice_data",
                 fetch_data=True,
                 store_data=True,
                 ):
        self.store_data = store_data
        self.data_base_dir = base_data_path
        if fetch_data and store_data:
            create_folder_if_not_exists(self.data_base_dir)
            if not os.path.exists(self.price_range_data_path):
                raw, processed = self.fetch_price_range_data()
                self.write_data(raw, self.raw_price_range_data_path)
                self.write_data(processed, self.price_range_data_path)
            if not os.path.exists(self.district_data_path):
                raw, processed = self.fetch_district_data()
                self.write_data(raw, self.raw_district_data_path)
                self.write_data(processed, self.district_data_path)

    def __repr__(self) -> str:
        return f"OpenriceApi(base_data_path={self.base_data_path}, store_data={self.store_data})"


if __name__ == "__main__":
    openriceApi = OpenriceApi()
    resault = openriceApi.search_restaurants({
        "keyword": "麵包",
        "start": "0",
        "count": 3,
        "district": "中環",
        "district_lang": "tc",
    })
    print(resault)

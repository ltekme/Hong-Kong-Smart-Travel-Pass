import os
import ChatLLM.Tools.Openrice.caller as openrice
from google.oauth2.service_account import Credentials

credentials_path = os.getenv(
    "GCP_AI_SA_CREDENTIAL_PATH", './gcp_cred-ai.json')
credentials = Credentials.from_service_account_file(credentials_path)

kwargs = {
    "verbose": True,
    "credentials": credentials
}
# filters = openrice.Filters(**kwargs)
searchEngine = openrice.RestaurantSearchApi(**kwargs)

resault = []

# resault.append(filters.search("dim sum"))
# "dishId": "1036", "nameEN": "Dim Sum", "nameTC": "點心", "nameSC": "点心"
# "dishId": "1039", "nameEN": "Wonton/Dumpling", "nameTC": "雲吞/餃子", "nameSC": "云吞/饺子"
# "amenityId": "1005", "nameEN": "Dim Sum Restaurant", "nameTC": "酒樓", "nameSC": "酒楼"
# "dishId": "1018", "nameEN": "Congee", "nameTC": "粥品", "nameSC": "粥品"
# "dishId": "1004", "nameEN": "Food Stall Noodles", "nameTC": "車仔麵", "nameSC": "车仔面"

# resault.append(filters.search("tiu king leng"))
# "districtId": "1026", "nameEN": "Tin Hau", "nameTC": "天后", "nameSC": "天后"
# "landmarkId": "35215", "nameEN": "Lee Tung Avenue", "nameTC": "利東街", "nameSC": "利东街"
# "landmarkId": "123", "nameEN": "Tai Hung Fai (Tsuen Wan) Centre", "nameTC": "大鴻輝(荃灣)中心", "nameSC": "大鸿辉（荃湾）中心"
# "landmarkId": "50", "nameEN": "King Wah Centre", "nameTC": "瓊華中心", "nameSC": "琼华中心"
# "landmarkId": "3012", "nameEN": "Lai King Station", "nameTC": "荔景站", "nameSC": "荔景站"

# resault.append(filters.search("hot pot"))
# "dishId": "1204", "nameEN": "Steam Hotpot", "nameTC": "蒸氣火鍋", "nameSC": "蒸气火锅"
# "dishId": "1001", "nameEN": "Hot Pot", "nameTC": "火鍋", "nameSC": "火锅"
# "dishId": "1074", "nameEN": "Chicken Hot Pot", "nameTC": "雞煲", "nameSC": "鸡煲"
# "dishId": "1040", "nameEN": "Hot Chili Oil", "nameTC": "水煮菜式", "nameSC": "水煮菜式"
# "dishId": "1082", "nameEN": "Big Bowl Feast", "nameTC": "盆菜", "nameSC": "盆菜"

resault.append(searchEngine.search(
    dishIds=[1204, 1001],
    landmarkIds=[1026],
    amenityIds=[1005],
))


for r in resault:
    print("="*30)
    for rest in r:
        print(searchEngine.to_beautify_string(rest))

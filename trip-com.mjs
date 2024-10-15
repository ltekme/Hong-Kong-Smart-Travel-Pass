import fs from 'node:fs';

export const tractionDataPath = './traction_data';
if (!fs.existsSync(tractionDataPath)) fs.mkdirSync(tractionDataPath);

const requestBody = {
  head: {
    // syscode: '',
    // lang: '',
    // auth: '',
    // cid: '1728913602112.4736Rgli22JR',
    // ctok: '',
    // cver: '',
    // sid: '8888',
    // extension: [
    //   {
    //     name: "bookingTransactionId",
    //     value: "1728990887154_1240"
    //   }
    // ],
    // pauth: '',
    // sauth: '',
    // appid: '100017626'
  },
  imageOption: { width: 568, height: 320 },
  requestSource: 'activity',
  destination: { keyword: 'kowloon' },
  filtered: { pageIndex: 1, sort: '1', pageSize: 20, tab: 'Ticket2', items: [] },
  productOption: {
    needBasicInfo: true,
    needComment: true,
    needPrice: true,
    needRanking: true,
    needVendor: true,
    tagOption: [
      'PRODUCT_TAG',
      'IS_AD_TAG',
      'PROMOTION_TAG',
      'FAVORITE_TAG',
      'GIFT_TAG',
      'COMMENT_TAG',
      'IS_GLOBALHOT_TAG'
    ]
  },
  searchOption: {
    filters: [],
    needAdProduct: true,
    returnMode: 'all',
    needUpStream: false
  },
  // extras: { needScenicSpotNewPrice: 'true', usingTicket2: 'true' },
  client: {
    // pageId: '10650012671',
    // crnVersion: '2023-12-06 20:13:56',
    // platformId: 24,
    // location: {
    //   cityId: null,
    //   cityType: null,
    //   locatedCityId: null,
    //   lat: '',
    //   lon: ''
    // },
    locale: 'zh-HK',
    currency: 'HKD',
    // channel: 118,
    // cid: '1728913602112.4736Rgli22JR',
    // trace: '8fbc3fa8-3d17-dd07-4091-172891c41825',
    // extras: { client_locatedDistrictId: 'undefined', client_districtId: '38' }
  }
}

console.log(requestBody);
await fs.writeFileSync(`${tractionDataPath}/trip_com_request.json`, JSON.stringify(requestBody, null, 4));

const response = await fetch("https://m.trip.com/restapi/soa2/20684/json/productSearch", {
  "headers": {
    "accept": "application/json",
    "accept-language": "en,en-US;q=0.9,en-GB;q=0.8,en-HK;q=0.7,zh-HK;q=0.6,zh;q=0.5",
    "cache-control": "no-cache",
    "content-type": "application/json;charset=UTF-8",
    "currency": "HKD",
    "locale": "zh-HK",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Google Chrome\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    // "cookie": "UBT_VID=1728913602112.4736Rgli22JR; cookiePricesDisplayed=HKD; _abtest_userid=e9d4d5b2-3847-403f-a4f7-56072a9c6f6e; ubtc_trip_pwa=0; _gid=GA1.2.342817412.1728913603; _gcl_au=1.1.427969713.1728913604; _RSG=OGKM.eNFFj085FjJe24kkA; _RDG=28640f88afca9c2e3d3bd2f09d0a533f6f; _RGUID=0b4f3d7a-3e59-4418-abae-102a13b4f148; _fbp=fb.1.1728913639510.963983668840274940; _bfaStatusPVSend=1; _ubtstatus=%7B%22vid%22%3A%221728913602112.4736Rgli22JR%22%2C%22sid%22%3A1%2C%22pvid%22%3A10%2C%22pid%22%3A0%7D; _bfaStatus=success; ibu_online_jump_site_result={\"site_url\":[],\"suggestion\":[]}; ibu_online_home_language_match={\"isRedirect\":false,\"isShowSuggestion\":false,\"lastVisited\":true,\"region\":\"hk\",\"redirectSymbol\":false}; _tt_enable_cookie=1; _ttp=rLVwQR6OLSudV7jNawpUj7EwXo5; _RF1=182.239.122.31; ibulocale=zh_hk; ibulanguage=HK; _gat=1; _gat_UA-109672825-3=1; _uetsid=d4d4bcc08a3211ef8148bf4f0cb1e1dd; _uetvid=d4d4bd108a3211efbb5d69c786a0db9b; _ga_37RNVFDP1J=GS1.2.1728990718.2.1.1728990873.21.0.0; _ga_2DCSB93KS4=GS1.2.1728990718.2.1.1728990874.21.0.0; _ga_X437DZ73MR=GS1.1.1728990718.2.1.1728990885.8.0.0; _bfa=1.1728913602112.4736Rgli22JR.1.1728990873370.1728990886810.2.8.10650012671; _ga=GA1.2.518438829.1728913603",
    "Referer": "https://hk.trip.com/",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
  },
  "body": JSON.stringify(requestBody),
  "method": "POST"
});
const responseData = await response.json()
await fs.writeFileSync(`${tractionDataPath}/trip_com.json`, JSON.stringify(responseData, null, 4));
console.log(responseData);
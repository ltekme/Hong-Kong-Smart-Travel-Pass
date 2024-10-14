import { getPriceRangeTextFromId, getDistrictNameFromId } from "./openriceMapping.mjs";

export const apiBaseUrl = "https://www.openrice.com/api/v2/search?uiLang=zh&uiCity=hongkong&regionId=0&pageToken=CONST_DUMMY_TOKEN";
export const headers = {
    "accept": "*/*",
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

export const formatResonseRestaurant = async (restaurant) => {
    return {
        name: restaurant.name,
        faviconUrl: restaurant.doorPhoto.url,
        address: restaurant.address,
        loction: {
            latitude: restaurant.mapLatitude,
            longitude: restaurant.mapLongitude,
        },
        priceRange: {
            text: (await getPriceRangeTextFromId(restaurant.priceRangeId)).nameLangDict.tc,
            id: restaurant.priceRangeId,
        },
        district: {
            id: restaurant.district.districtId,
            text: (await getDistrictNameFromId(restaurant.district.districtId)).nameLangDict.tc,
        },
        contectInfo: {
            openRiceShortUrl: restaurant.shortenUrl,
            phones: restaurant.phones,
        },
    }
}

export const searchOpenRiceApi = async ({ whatwere, from, n, districtId }) => {
    let params = ''
    params += from ? `&startAt=${from}` : `&startAt=0`
    params += n ? `&rows=${n}` : `&rows=3`
    params += whatwere ? `&whatwhere=${whatwere}` : null
    params += districtId ? `&districtId=${districtId}` : null
    if (!whatwere && !districtId) {
        throw new Error('Please provide either whatwere or districtId')
    }

    let response = await fetch(apiBaseUrl + params, {
        headers: headers,
        body: null,
        method: "GET",
    });
    if (!response.ok) {
        throw new Error('Cannot fetch api')
    }

    let responseJson = await response.json();
    let resault = responseJson.paginationResult.results;
    return Promise.all(resault.map(formatResonseRestaurant));
}

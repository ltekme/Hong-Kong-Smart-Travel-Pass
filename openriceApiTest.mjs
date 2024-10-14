import { searchOpenRiceApi } from "./openriceApiSearch.mjs";
import { convertLatitudeLongitudeToGoogleMapUrl, getDistrictIdfromName } from "./openriceMapping.mjs";

const whatwere = "dim sum";
const from = 0;
const n = 3;
const district = '中環';
const districtLang = 'tc';
// {
//     name: '',
//     faviconUrl: '',
//     address: '',
//     loction: { latitude: 22.0000000, longitude: 114.0000000 },
//     priceRange: { text: '$201-400', id: 4 },
//     district: { id: 1003, text: '中環' },
//     contectInfo: {
//       openRiceShortUrl: '',
//       phones: [ '' ]
//     }
//   }

const prettyPrintResault = (restaurant) => {
    console.log(`-`.repeat(100));
    console.log(`Name: ${restaurant.name}`);
    console.log(`Address: ${restaurant.address}`);
    console.log(`Price Range: ${restaurant.priceRange.text}`);
    console.log(`District: ${restaurant.district.text}`);
    console.log(`Phone: ${restaurant.contectInfo.phones.join(', ')}`);
    console.log(`Google Map Url: ${convertLatitudeLongitudeToGoogleMapUrl(restaurant.loction.latitude, restaurant.loction.longitude)}`);
    console.log(`OpenRice Short Url: ${restaurant.contectInfo.openRiceShortUrl}`);
    console.log(`Cover Image Url: ${restaurant.faviconUrl}`);
    console.log(`-`.repeat(100))
}

let response = await searchOpenRiceApi({
    whatwere: whatwere,
    from: from,
    n: n,
    districtId: await getDistrictIdfromName(district, districtLang)
});

console.log('Search param: keyward:', whatwere, ', resault count:', n, ', starting from: ', from, ', district name:', district, ', district lang:', districtLang);

for (response of response) {
    prettyPrintResault(response);
};
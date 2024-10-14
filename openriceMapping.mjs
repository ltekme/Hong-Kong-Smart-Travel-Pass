import fs from 'node:fs';

export const langOption = ['tc', 'en', 'sc'];

export const rawPriceRangeApiUrl = 'https://www.openrice.com/api/v2/metadata/country/all';
export const rawDistrictApiUrl = 'https://www.openrice.com/api/v2/metadata/region/all?uiLang=zh&uiCity=hongkong';

export const baseDataPath = './data/';
export const rawDistrictDataPath = baseDataPath + 'openrice_district_raw.json';
export const processDistrictDataPath = baseDataPath + 'openrice_district_processed.json';
export const rawPriceRangeDataPath = baseDataPath + 'openrice_priceRange_raw.json';
export const processPriceRangeDataPath = baseDataPath + 'openrice_priceRange_processed.json';

export const fetchDataFromUrl = async (url) => {
    const data = await fetch(url);
    return await data.json();
};

export const createFolderIfNotExist = async (path) => {
    return await fs.existsSync(path) ? true : await fs.mkdirSync(path);
};

export const getPriceRangeTextFromId = async (priceRangeId) => {
    if (!fs.existsSync(processPriceRangeDataPath)) {
        console.error('District data not found. Fetching from API.');
        await processPriceRange();
    }
    const priceRange = await JSON.parse(fs.readFileSync(processPriceRangeDataPath, 'utf8'));
    return priceRange.find(priceRange => priceRange.priceRangeId === priceRangeId);
};

export const getDistrictNameFromId = async (districtId) => {
    if (!fs.existsSync(processDistrictDataPath)) {
        console.error('District data not found. Fetching from API.');
        await processDistrict();
    }
    const district = await JSON.parse(fs.readFileSync(processDistrictDataPath, 'utf8'));
    return district.find(district => district.districtId === districtId);
};

// https://www.google.com/maps/place/22.2814411,114.1564406
export const convertLatitudeLongitudeToGoogleMapUrl = (mapLatitude, mapLongitude) => {
    const googleMapPlaceUrl = "https://www.google.com/maps/place/"
    return `${googleMapPlaceUrl}${mapLatitude},${mapLongitude}`;
};

export const getDistrictIdfromName = async (districtName, lang) => {
    if (langOption.indexOf(lang) === -1) {
        throw new Error('Invalid language option: ' + lang);
    }
    if (!fs.existsSync(processDistrictDataPath)) {
        console.error('District data not found. Fetching from API.');
        await processDistrict();
    }
    const district = await JSON.parse(fs.readFileSync(processDistrictDataPath, 'utf8'));
    return district.find(district => district.nameLangDict[lang] === districtName).districtId;
};

// https://www.openrice.com/api/v2/metadata/country/all
export const processPriceRange = async () => {
    console.log('Processing price range data...');
    if (!fs.existsSync(rawPriceRangeDataPath)) {
        await createFolderIfNotExist(baseDataPath);
        console.error('Price range data not found. Fetching from API.');
        let data = await fetchDataFromUrl(rawPriceRangeApiUrl);
        await fs.writeFileSync(rawPriceRangeDataPath, JSON.stringify(data, null, 4));
    }
    const rawPriceRange = await JSON.parse(fs.readFileSync(rawPriceRangeDataPath, 'utf8'));
    let processedPriceRange = rawPriceRange.regions['0'].priceRanges.map(priceRange => {
        return {
            priceRangeId: priceRange.priceRangeId,
            nameLangDict: {
                tc: priceRange.nameLangDict.tc,
                en: priceRange.nameLangDict.en,
                sc: priceRange.nameLangDict.sc,
            },
            nameId: `from-${priceRange.rangeStart}-to-${priceRange.rangeEnd}`,
        }
    });
    await fs.writeFileSync(processPriceRangeDataPath, JSON.stringify(processedPriceRange, null, 4));
    console.log('Price range processed data saved.');
};

export const processDistrict = async () => {
    console.log('Processing district data...');
    // https://www.openrice.com/api/v2/metadata/region/all?uiLang=zh&uiCity=hongkong
    if (!fs.existsSync(rawDistrictDataPath)) {
        console.error('District data not found. Fetching from API.');
        await createFolderIfNotExist(baseDataPath);
        let data = await fetchDataFromUrl(rawDistrictApiUrl);
        await fs.writeFileSync(rawDistrictDataPath, JSON.stringify(data, null, 4));
    }
    const rawDistrict = await JSON.parse(fs.readFileSync(rawDistrictDataPath, 'utf8'));
    let processedDistict = rawDistrict.districts.map(distict => {
        return {
            districtId: distict.districtId,
            nameLangDict: {
                tc: distict.nameLangDict.tc,
                en: distict.nameLangDict.en,
                sc: distict.nameLangDict.sc,
            },
            nameId: distict.callNameLangDict.en,
        }
    });
    await fs.writeFileSync(processDistrictDataPath, JSON.stringify(processedDistict, null, 4));
    console.log('District processed data saved.');
};

// Uncomment to fetch district and priceRange data
// await Promise.all([processDistrict(), processPriceRange()]);
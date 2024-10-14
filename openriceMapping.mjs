import fs from 'node:fs';

export const getPriceRangeTextFromId = async (priceRangeId) => {
    const priceRange = await JSON.parse(fs.readFileSync('./data/openrice_priceRange_processed.json', 'utf8'));
    return priceRange.find(priceRange => priceRange.priceRangeId === priceRangeId);
}

export const getDistrictNameFromId = async (districtId) => {
    const district = await JSON.parse(fs.readFileSync('./data/openrice_district_processed.json', 'utf8'));
    return district.find(district => district.districtId === districtId);
}

// https://www.openrice.com/api/v2/metadata/country/all
export const processPriceRange = async () => {
    console.log('Processing price range data...');
    const rawPriceRange = await JSON.parse(fs.readFileSync('./data/openrice_priceRange_raw.json', 'utf8'));
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
    await fs.writeFileSync(`./data/openrice_priceRange_processed.json`, JSON.stringify(processedPriceRange, null, 4));
    console.log('Price range processed data saved.');
};

export const processDistrict = async () => {
    console.log('Processing district data...');
    // https://www.openrice.com/api/v2/metadata/region/all?uiLang=zh&uiCity=hongkong
    const rawDistrict = await JSON.parse(fs.readFileSync('./data/openrice_district_raw.json', 'utf8'));
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
    await fs.writeFileSync(`./data/openrice_district_processed.json`, JSON.stringify(processedDistict, null, 4));
    console.log('District processed data saved.');
};

// Uncomment to fetch district and priceRange data
// await Promise.all([processDistrict(), processPriceRange()]);
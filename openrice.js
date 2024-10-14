const fs = require('node:fs');

// get from chrome dev tools
fetch("https://www.openrice.com/api/v2/search?uiLang=en&regionId=0&startAt=0&rows=15&pageToken=CONST_DUMMY_TOKEN", {
    "headers": {
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
    },
    "body": null,
    "method": "GET"
})
    .then(response => response.json())
    .then(async data => {
        // console.log(JSON.stringify(data));
        await fs.writeFileSync(`./data/openrice_raw.json`, JSON.stringify(data, null, 4));
        await fs.writeFileSync(`./data/openrice_resault.json`, JSON.stringify(data.paginationResult.results, null, 4));

    }).catch(err => {
        console.log(err);
    });
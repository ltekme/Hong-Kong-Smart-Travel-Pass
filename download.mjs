// const fs = require('node:fs');
import fs from 'node:fs';

let urls = `https://static.data.gov.hk/td/routes-fares-geojson/JSON_BUS.json
https://static.data.gov.hk/td/routes-fares-geojson/JSON_GMB.json
https://static.data.gov.hk/td/routes-fares-geojson/JSON_FERRY.json
https://static.data.gov.hk/td/routes-fares-geojson/JSON_PTRAM.json
https://static.data.gov.hk/td/routes-fares-geojson/JSON_TRAM.json
https://opendata.mtr.com.hk/data/mtr_lines_and_stations.csv
https://opendata.mtr.com.hk/data/light_rail_routes_and_stops.csv
https://opendata.mtr.com.hk/data/mtr_bus_routes.csv
https://opendata.mtr.com.hk/data/mtr_lines_fares.csv
https://opendata.mtr.com.hk/data/mtr_bus_stops.csv`

let urlsArray = urls.split('\n')

const download = async (url) => {
  let data = await fetch(url);
  if (!url.endsWith('json')) {
    await fs.writeFileSync(`./data/${url.split('/').pop()}`, await data.text());
    console.log(`Downloaded ${url.split('/').pop()}`)
    return true
  }
  let json_data = await data.json();
  await fs.writeFileSync(`./data/${url.split('/').pop()}`, JSON.stringify(json_data, null, 4));
  console.log(`Downloaded ${url.split('/').pop()}`)
  return true
}

if (!fs.existsSync("data")) {
  fs.mkdirSync("data");
}

const downloadTasks = []
urlsArray.forEach(url => {
  let fileName = url.split('/').pop()
  console.log(`Starting download ${fileName} to ./data/${fileName}`)
  downloadTasks.push(download(url))
})
Promise.all(downloadTasks)
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


const dataFolder = "./data"

const download = async (url) => {
  const fileName = url.split('/').pop()
  console.log(`Starting download ${fileName} to ${dataFolder}/${fileName}`)
  let data = await fetch(url);
  
  // non-josn file
  if (!url.endsWith('json')) {
    await fs.writeFileSync(`${dataFolder}/${fileName}`, await data.text());
    console.log(`Downloaded ${fileName}`)
    return true
  }
  
  let json_data = await data.json();
  await fs.writeFileSync(`${dataFolder}/${fileName}`, JSON.stringify(json_data, null, 4));
  console.log(`Downloaded ${fileName}`)
  return true
}

if (!fs.existsSync("data")) {
  fs.mkdirSync("data");
}

Promise.all(urls.split('\n').map(download))
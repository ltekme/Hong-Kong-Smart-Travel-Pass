// const fs = require('node:fs');
import fs from 'node:fs'

let urls = `https://static.data.gov.hk/td/routes-fares-geojson/JSON_BUS.json
https://static.data.gov.hk/td/routes-fares-geojson/JSON_GMB.json
https://static.data.gov.hk/td/routes-fares-geojson/JSON_FERRY.json
https://static.data.gov.hk/td/routes-fares-geojson/JSON_PTRAM.json
https://static.data.gov.hk/td/routes-fares-geojson/JSON_TRAM.json`

let urlsArray = urls.split('\n')

const dataPath = './transport_data'

const download = async (url) => {
  let data = await fetch(url);
  let json_data = await data.json();
  await fs.writeFileSync(`./${dataPath}/${url.split('/').pop()}`, JSON.stringify(json_data, null, 4));
  console.log(`Downloaded ${url.split('/').pop()}`)
  return true
}

await !fs.existsSync(dataPath) ? fs.mkdirSync(dataPath) : null

const downloadTasks = []
urlsArray.map(url => {
  let fileName = url.split('/').pop()
  console.log(`Starting download ${fileName} to ./data/${fileName}`)
  downloadTasks.push(download(url))
})
Promise.all(downloadTasks)
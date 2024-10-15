import fs from 'node:fs';

const transportDataPath = './transport_data';

const transportDataPathFiles = await fs.readdirSync(transportDataPath);
const transportDataFiles = transportDataPathFiles.filter(file => file.startsWith('JSON') && file.endsWith('.json'));
console.log(`Loading files: \x1b[32m${transportDataFiles.join('\x1b[0m, \x1b[32m')}\x1b[0m`);

let csvRows = [];
let headersWritten = false;

const transformToCsv = async (file) => {
    const fileData = (JSON.parse(await fs.readFileSync(file, 'utf8'))).features;
    console.log(`Transforming \x1b[33m${file}\x1b[0m to CSV, item count: \x1b[33m${fileData.length}\x1b[0m`);

    let thisCsvRows = [];

    // Write headers
    let headers = [];
    Object.keys(fileData[0].properties).forEach(key => {
        if (key.startsWith('hyperlink')) return;
        headers.push(key);
    });
    headers.push("longitude", "latitude");
    thisCsvRows.push(headers.join(','));
    if (!headersWritten) {
        headersWritten = true;
        csvRows.push(headers.join(','));
    };

    // Write data
    fileData.forEach(data => {
        let row = [];
        Object.keys(data.properties).forEach(key => {
            if (key.startsWith('hyperlink')) return;
            let value = data.properties[key].toString();
            value = value.includes(',') ? value.replace(',', '-') : value;
            value = value.includes('\n') ? value.replace('\n', ' ') : value;
            value = value.includes('\r') ? value.replace('\r', ' ') : value;
            value = value === "" ? 'N/A' : value;
            row.push(value);
        });
        row.push(data.geometry.coordinates[0], data.geometry.coordinates[1]);
        csvRows.push(row.join(','));
        thisCsvRows.push(row.join(','));
    });

    await fs.writeFileSync(file.replace('.json', '.csv').replace('JSON_', 'CSV_'), thisCsvRows.join('\n'));
    console.log(`Transformed \x1b[31m${file}\x1b[0m -> \x1b[32m${file.replace('.json', '.csv').replace('JSON_', 'CSV_')}\x1b[0m`);
};

let job = [];

transportDataFiles.map(file => job.push(transformToCsv(transportDataPath + '/' + file)));
await Promise.all(job);

// Write combined CSV
await fs.writeFileSync(transportDataPath + '/combined.csv', csvRows.join('\n'));
console.log(`Combined CSV written to \x1b[32mcombined.csv\x1b[0m`);
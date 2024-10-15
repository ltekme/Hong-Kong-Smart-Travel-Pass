import fs from 'node:fs';

const transportDataPath = './transport_data';

const transportDataPathFiles = await fs.readdirSync(transportDataPath);
const transportDataFiles = transportDataPathFiles.filter(file => file.startsWith('JSON') && file.endsWith('.json'));
console.log(`Loading files: \x1b[32m${transportDataFiles.join('\x1b[0m, \x1b[32m')}\x1b[0m`);

const transformToCsv = async (file) => {
    const fileData = (JSON.parse(await fs.readFileSync(file, 'utf8'))).features;
    console.log(`Transforming \x1b[33m${file}\x1b[0m to CSV, item count: \x1b[33m${fileData.length}\x1b[0m`);
    let csvRow = '';

    // Write headers
    Object.keys(fileData[0].properties).forEach(async key => {
        if (key.startsWith('hyperlink')) return;
        csvRow += key + ',';
    });
    csvRow += "longitude,latitude\n";

    // Write data
    fileData.forEach(data => {
        Object.keys(data.properties).forEach(key => {
            if (key.startsWith('hyperlink')) return;
            if (data.properties[key].toString().includes(',')) {
                data.properties[key] = `"${data.properties[key].replace(',', '-')}"`;
            }
            if (data.properties[key].toString().includes('\n')) {
                data.properties[key] = `"${data.properties[key].replace('\n', ' ')}"`;
            }
            if (data.properties[key].toString().includes('\r')) {
                data.properties[key] = `"${data.properties[key].replace('\r', ' ')}"`;
            }
            if (data.properties[key] === '') {
                data.properties[key] = 'N/A';
            }
            csvRow += `${data.properties[key]},`;
        });
        csvRow += `${data.geometry.coordinates[0]},${data.geometry.coordinates[1]}\n`;
    });

    await fs.writeFileSync(file.replace('.json', '.csv').replace('JSON_', 'CSV_'), csvRow);
    console.log(`Transformed \x1b[31m${file}\x1b[0m -> \x1b[32m${file.replace('.json', '.csv').replace('JSON_', 'CSV_')}\x1b[0m`);
};
let job = [];
transportDataFiles.map(file => job.push(transformToCsv(transportDataPath + '/' + file)));

Promise.all(job)
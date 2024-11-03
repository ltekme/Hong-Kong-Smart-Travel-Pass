function sumOf (a,b, callback) {
    callback(a+b);
}

function outputToConsole (msg) {
    console.log(msg);
}

sumOf(1, 2, outputToConsole);
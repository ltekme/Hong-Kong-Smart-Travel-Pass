import { searchOpenRiceApi } from "./openriceApiSearch.mjs";

const whatwere = "dim sum";
const from = 0;
const n = 5;

let response = await searchOpenRiceApi(whatwere, from, n);
response.forEach(element => {
    console.log(element);
});
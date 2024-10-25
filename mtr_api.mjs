const queryParams = "lang=E&oLabel=Kowloon&oType=HRStation&oValue=45&dLabel=Disneyland%20Resort&dType=HRStation&dValue=55"
const resault = await fetch(`https://www.mtr.com.hk/share/customer/jp/api/CompleteRoutes/?${queryParams}`, {
    "headers": {
      "accept": "*/*",
      "accept-language": "en,en-US;q=0.9,en-GB;q=0.8,en-HK;q=0.7,zh-HK;q=0.6,zh;q=0.5",
      "cache-control": "no-cache",
      "pragma": "no-cache",
      "priority": "u=1, i",
      "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "\"Windows\"",
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-origin",
      "x-requested-with": "XMLHttpRequest",
      // "cookie": "ARRAffinity=293dca6e50e0448949dd1b45076f4b3ede6f3ebe0a3cf1228b4fe209661d3bbf; ARRAffinitySameSite=293dca6e50e0448949dd1b45076f4b3ede6f3ebe0a3cf1228b4fe209661d3bbf; gLang=E; gTour=L; PHPSESSID=km5q5f7tmu828vim5l4a5ab745; style_val=styles1; _gid=GA1.3.475086806.1729840804; jphistory=%7B%7D; ARRAffinity=293dca6e50e0448949dd1b45076f4b3ede6f3ebe0a3cf1228b4fe209661d3bbf; ARRAffinitySameSite=293dca6e50e0448949dd1b45076f4b3ede6f3ebe0a3cf1228b4fe209661d3bbf; _gid=GA1.3.475086806.1729840804; _gat_UA-109329221-3=1; _ga=GA1.1.2001646916.1729840804; _ga_Y6KEBZX3W9=GS1.1.1729840804.1.1.1729841677.0.0.0; ai_user=1A0995EF-3EF7-4D42-BB4A-4B23553BED9E; _ga_Y6KEBZX3W9=GS1.1.1729840804.1.1.1729841694.0.0.0; _ga=GA1.1.2001646916.1729840804",
      // "Referer": "https://www.mtr.com.hk/en/customer/jp/index.php?oLabel=Kowloon&oType=HRStation&oValue=45&dLabel=Disneyland%20Resort&dType=HRStation&dValue=55",
      "Referrer-Policy": "no-referrer-when-downgrade"
    },
    "body": null,
    "method": "GET"
  });

const data = await resault.json();
console.log(data);
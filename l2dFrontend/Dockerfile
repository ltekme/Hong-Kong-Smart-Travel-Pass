FROM node:latest as build
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./package-lock.json /usr/src/app/package-lock.json
COPY ./package.json /usr/src/app/package.json
COPY ./tsconfig.json /usr/src/app/tsconfig.json
COPY ./src /usr/src/app/src
COPY ./public /usr/src/app/public

RUN npm install
RUN npm run build

FROM nginx:stable-alpine
COPY --from=build /usr/src/app/build /usr/share/nginx/html
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

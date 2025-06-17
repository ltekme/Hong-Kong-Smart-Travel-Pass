FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt install npm python3 python3-pip python3.12-venv -y
ENV DEBIAN_FRONTEND=dialog

RUN mkdir /app
RUN mkdir /opt/venv

WORKDIR /app

RUN python3 -m venv /opt/venv
COPY ./requirements.txt /app/requirements.txt
RUN /opt/venv/bin/pip install -r requirements.txt

COPY ./app.py /app/app.py
COPY ./APIv2 /app/APIv2
COPY ./ChatLLM /app/ChatLLM
COPY ./ChatLLMv2 /app/ChatLLMv2

ENTRYPOINT [ "/opt/venv/bin/python", "/app/app.py" ]
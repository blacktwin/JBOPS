FROM python:3-slim

WORKDIR /usr/src/app

COPY . ./
RUN pip install -r requirements.txt

RUN mkdir -p /root/.config/plexapi
RUN cp config.ini /root/.config/plexapi/config.ini
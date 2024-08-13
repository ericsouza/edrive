FROM python:3.12.5-slim

ENV DEPLOYMENT_MODE=docker

WORKDIR /app

RUN mkdir -p ./files

ADD main.py ./main.py

ENTRYPOINT [ "python", "main.py" ]

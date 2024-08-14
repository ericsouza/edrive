FROM python:3.12.5-slim

ENV DEPLOYMENT_MODE=docker

WORKDIR /app

RUN mkdir -p ./manager/files

ADD requirements.txt requirements.txt
ADD manager/ manager/
ADD entrypoint.sh entrypoint.sh

RUN pip install -r requirements.txt

ENTRYPOINT [ "./entrypoint.sh" ]

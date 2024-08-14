FROM python:3.12.5-slim

ENV DEPLOYMENT_MODE=docker

WORKDIR /app

RUN mkdir -p ./files
ADD requirements.txt requirements.txt
ADD main.py ./main.py
ADD db.py ./db.py

RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "main.py" ]

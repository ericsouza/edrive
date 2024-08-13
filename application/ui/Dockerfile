FROM python:3.12.5-slim

WORKDIR /app

RUN mkdir -p ./files

ADD requirements.txt requirements.txt
ADD app.py app.py
ADD db.py db.py
ADD templates/ templates/

RUN pip install -r requirements.txt

ENTRYPOINT [ "waitress-serve", "--host", "0.0.0.0", "--port", "5000", "app:app" ]


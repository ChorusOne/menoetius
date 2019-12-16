FROM python:3.7-alpine3.10

COPY . /menoetius

WORKDIR /menoetius

RUN pip3 install -r requirements.txt

CMD python3 /menoetius/menoetius.py

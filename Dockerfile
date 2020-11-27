FROM python:3.9-alpine3.12

COPY . /menoetius

WORKDIR /menoetius

RUN pip3 install -r requirements.txt

CMD python3 /menoetius/menoetius.py

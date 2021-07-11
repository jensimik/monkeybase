FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim
# use -slim and not -alpine as then wheel packages work

RUN apt-get update && apt-get -y install git

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY ./backend /backend

WORKDIR /backend

ENV PYTHONPATH=/backend
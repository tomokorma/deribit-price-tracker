FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED 1

RUN apt-get -q update \
    && apt-get -q -y --no-install-recommends install libev4 libev-dev gcc libc6-dev wget

WORKDIR /opt/backend

COPY ./src/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip wheel \
    && pip install --no-cache-dir -r requirements.txt

RUN apt-get -q -y purge libev-dev gcc libc6-dev wget \
    && apt-get -q -y autoremove \
    && apt-get -q -y clean \
    && apt-get -q -y autoclean

COPY ./src/. ./

ENTRYPOINT ["python", "main.py"]

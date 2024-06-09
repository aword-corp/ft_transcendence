FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
	gcc \
	libpq-dev

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY conf/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

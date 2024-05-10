FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
	gcc \
	libpq-dev \
	curl

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY conf/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

ADD backend /app/backend

WORKDIR /app/backend

COPY tools/entrypoint.sh /app/backend/entrypoint.sh
RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 8000

CMD ["/app/backend/entrypoint.sh"]

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
	python3-full \
	python3-pip

RUN apt-get update && apt-get install -y \
	python3-django

ADD djangotest /djangotest

EXPOSE 8000

CMD ["python3" "/djangotest/manage.py" "runserver"]

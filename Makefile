COMPOSE_FILE = srcs/docker-compose.yml
DJANGO_BASE_DIR = srcs/django/
GIT_TAG := $(shell git rev-parse --short HEAD)
DJANGO_BASE_TAG = acorp/django-base:$(GIT_TAG)
DJANGO_LATEST_TAG = acorp/django-base:latest

ifeq ($(dev),true)
    COMPOSE_FILE = srcs/docker-compose-dev.yml
endif

ENV_FILE = srcs/.env

all: build
	$(MAKE) run

build: $(ENV_FILE)
	docker build -t $(DJANGO_BASE_TAG) -t $(DJANGO_LATEST_TAG) $(DJANGO_BASE_DIR)
	docker compose -f $(COMPOSE_FILE) build

run: $(ENV_FILE)
	docker compose -f $(COMPOSE_FILE) up -d --remove-orphans

re: fclean
	$(MAKE) build
	$(MAKE) run

stop:
	docker compose -f $(COMPOSE_FILE) stop

repurge: purge
	$(MAKE) build
	$(MAKE) run

status:
	docker compose -f $(COMPOSE_FILE) ps

logs:
	docker compose -f $(COMPOSE_FILE) logs

fclean:
	docker compose -f $(COMPOSE_FILE) down

purge:
	docker compose -f $(COMPOSE_FILE) down -v --rmi all
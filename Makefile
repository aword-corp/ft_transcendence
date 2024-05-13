COMPOSE_FILE = srcs/docker-compose.yml

ifeq ($(dev),true)
    COMPOSE_FILE = srcs/docker-compose-dev.yml
endif

ENV_FILE = srcs/.env

all: build
	$(MAKE) run

build: $(ENV_FILE)
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
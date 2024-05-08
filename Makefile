COMPOSE_FILE = srcs/docker-compose.yml

ifeq ($(dev),true)
    COMPOSE_FILE = srcs/docker-compose-dev.yml
endif

ENV_FILE = srcs/.env

all: build
ifeq ($(dev),true)
	make run dev=true
else
	make run
endif

build: $(ENV_FILE)
	docker compose -f $(COMPOSE_FILE) build

run: $(ENV_FILE)
	docker compose -f $(COMPOSE_FILE) up -d --remove-orphans

re: fclean
	make build
	make run

stop:
	docker compose -f $(COMPOSE_FILE) stop

repurge: purge
	make build
	make run
status:
	docker compose -f $(COMPOSE_FILE) ps

logs:
	docker compose -f $(COMPOSE_FILE) logs

fclean:
	docker compose -f $(COMPOSE_FILE) down

purge: fclean
	docker system prune -af --volumes

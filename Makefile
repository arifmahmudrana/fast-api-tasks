# Makefile for FastAPI User System

# Variables
DOCKER_COMPOSE=docker-compose
PYTHON=python3
PIP=pip
VENV=.venv
APP=app.main:app
UVICORN=.venv/bin/uvicorn
ALEMBIC=.venv/bin/alembic
PYTEST=.venv/bin/pytest

# Docker Compose
up:
	$(DOCKER_COMPOSE) up --build

down:
	$(DOCKER_COMPOSE) down -v

# Local development
venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/$(PIP) install -r requirements.txt

run:
	$(UVICORN) $(APP) --reload

# Alembic migrations
migrate:
	PYTHONPATH=. $(ALEMBIC) upgrade head

# Testing
# Spin up MySQL in Docker, run tests, then clean up
mysql-test-up:
	docker run --name fastapi-mysql-test -e MYSQL_ROOT_PASSWORD=example -e MYSQL_DATABASE=fastapi_db_test -p 3307:3306 -d mysql:8.0

test: mysql-test-up venv
	# Wait for MySQL to be ready
	sleep 20
	PYTHONPATH=. MYSQL_HOST=127.0.0.1 MYSQL_PORT=3307 MYSQL_USER=root MYSQL_PASSWORD=example MYSQL_DATABASE=fastapi_db_test $(PYTEST)
	$(MAKE) coverage
	$(MAKE) mysql-test-down

mysql-test-down:
	docker rm -f fastapi-mysql-test || true

# Coverage
coverage:
	PYTHONPATH=. pytest --cov=app --cov=tests --cov-report=term-missing --cov-report=html

# Clean up all Docker containers and volumes
docker-clean:
	docker system prune -af --volumes

mongo-up:
	docker start mongo || docker run --name mongo -d -p 27017:27017 mongo:6.0

mongo-down:
	docker stop mongo || true
	docker rm mongo || true

.PHONY: up down venv run migrate test mysql-test-up mysql-test-down coverage docker-clean mongo-up mongo-down

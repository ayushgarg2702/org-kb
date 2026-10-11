.PHONY: install check lint type test test-unit test-acceptance migrate up down preflight bootstrap serve web-install web-dev

install:
	pip install -e ".[dev]"

lint:
	ruff check src tests
	ruff format --check src tests

format:
	ruff format src tests
	ruff check --fix src tests

type:
	mypy src/org_brain

test:
	pytest -q

test-unit:
	pytest -q tests/unit

test-acceptance:
	pytest -q tests/acceptance

check: lint type test

up:
	docker compose -f deploy/compose/docker-compose.yml up -d

down:
	docker compose -f deploy/compose/docker-compose.yml down

migrate:
	alembic upgrade head

preflight:
	org-brain preflight

bootstrap:
	org-brain bootstrap

serve:
	org-brain serve

web-install:
	cd web && npm install

web-dev:
	cd web && npm run dev

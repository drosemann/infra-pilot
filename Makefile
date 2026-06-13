.PHONY: setup dev dev-services dev-services-down test test-coverage lint format clean help healthcheck

setup:
	@bash scripts/setup.sh

dev:
	@docker compose up -d postgres redis && \
		npm run dev --prefix services/management-panel

dev-services:
	@docker compose up -d

dev-services-down:
	@docker compose down

test:
	@pytest tests/ -v

test-coverage:
	@pytest tests/ --cov=services

lint:
	@npm run lint --prefix services/management-panel

format:
	@prettier --write "services/**/*.{ts,tsx,js,jsx}"

clean:
	@docker compose down -v && rm -rf node_modules

help:
	@echo "Available commands: setup dev dev-services test lint format clean healthcheck"

healthcheck:
	bash ./scripts/healthcheck.sh

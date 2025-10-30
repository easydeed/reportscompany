.PHONY: db-up db-down migrate dev status

db-up:
	docker compose up -d

db-down:
	docker compose down -v

migrate:
	bash scripts/migrate.sh

dev:
	bash scripts/dev.sh

status:
	docker compose ps


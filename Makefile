.PHONY: dev backend frontend install typegen stop kill
.ONESHELL:

BACK_HOST=localhost
BACK_PORT=8010
FRONT_PORT=3010
DB_URL=postgresql+asyncpg://postgres@127.0.0.1:5432/loan_manager
# Use the uv-managed environment that `uv pip` installed to
PYTHON?=/Users/sam/Documents/.venv/bin/python
LOG_DIR=.devlogs

install:
	uv pip install -r backend/requirements.txt
	cd frontend && npm install

db:
	# Ensure DATABASE_URL is set, e.g., export DATABASE_URL=postgresql://localhost:5432/loan_manager
	@[ -n "$$DATABASE_URL" ] || (echo "DATABASE_URL is not set" && exit 1)
	psql "$$DATABASE_URL" -f database/migrations/0001_init.sql
	psql "$$DATABASE_URL" -f database/migrations/0002_idempotency.sql
	psql "$$DATABASE_URL" -f database/migrations/0003_webhooks.sql
	psql "$$DATABASE_URL" -f database/migrations/0004_bicycle_hire_purchase.sql
	psql "$$DATABASE_URL" -f database/migrations/0005_hr_module.sql
	psql "$$DATABASE_URL" -f database/migrations/0006_workshop_module.sql
	psql "$$DATABASE_URL" -f database/migrations/0007_rename_user_metadata.sql
	psql "$$DATABASE_URL" -f database/seed.sql
	psql "$$DATABASE_URL" -f database/seed_bicycle_system.sql

typegen:
	cd frontend && npm run typegen

backend:
	LM_DATABASE_URL=$(DB_URL) $(PYTHON) -m uvicorn app.main:app --app-dir backend --reload --host $(BACK_HOST) --port $(BACK_PORT)

frontend:
	cd frontend && PORT=$(FRONT_PORT) NEXT_PUBLIC_API_BASE_URL=http://$(BACK_HOST):$(BACK_PORT) npm run dev

dev:
	# Run both with hot reload and stop both on Ctrl+C
	set -e
	LM_DATABASE_URL=$(DB_URL) $(PYTHON) -m uvicorn app.main:app --app-dir backend --reload --host $(BACK_HOST) --port $(BACK_PORT) &
	BACK_PID=$$!
	cd frontend && PORT=$(FRONT_PORT) NEXT_PUBLIC_API_BASE_URL=http://$(BACK_HOST):$(BACK_PORT) npm run dev &
	FRONT_PID=$$!
	trap 'kill -INT $$BACK_PID $$FRONT_PID 2>/dev/null || true' INT TERM
	wait

stop:
	- pkill -f "uvicorn .*app.main:app" || true
	- pkill -f "next dev" || true
	- lsof -ti tcp:$(BACK_PORT) | xargs kill -9 2>/dev/null || true

kill:
	@echo "Killing processes on ports $(BACK_PORT) and $(FRONT_PORT)..."
	- lsof -ti tcp:$(BACK_PORT) | xargs kill -9 2>/dev/null || true
	- lsof -ti tcp:$(FRONT_PORT) | xargs kill -9 2>/dev/null || true
	- pkill -9 -f "uvicorn .*app.main:app" 2>/dev/null || true
	- pkill -9 -f "next dev" 2>/dev/null || true
	@echo "Done"

# Start both without killing on exit; leaves processes running
up:
	mkdir -p $(LOG_DIR)
	@lsof -ti tcp:$(BACK_PORT) >/dev/null || ( \
	  echo "Starting backend on $(BACK_HOST):$(BACK_PORT)"; \
	  LM_DATABASE_URL=$(DB_URL) $(PYTHON) -m uvicorn app.main:app --app-dir backend --reload --host $(BACK_HOST) --port $(BACK_PORT) > $(LOG_DIR)/backend.log 2>&1 & echo $$! > .backend.pid \
	)
	@lsof -ti tcp:$(FRONT_PORT) >/dev/null || ( \
	  echo "Starting frontend on :$(FRONT_PORT)"; \
	  cd frontend && PORT=$(FRONT_PORT) NEXT_PUBLIC_API_BASE_URL=http://$(BACK_HOST):$(BACK_PORT) npm run dev > ../$(LOG_DIR)/frontend.log 2>&1 & echo $$! > ../.frontend.pid \
	)
	@echo "Backend PID: $$(cat .backend.pid 2>/dev/null || echo running)"
	@echo "Frontend PID: $$(cat .frontend.pid 2>/dev/null || echo running)"

status:
	@echo "Backend listening on $(BACK_PORT): $$(lsof -ti tcp:$(BACK_PORT) || echo not running)"
	@echo "Frontend listening on $(FRONT_PORT): $$(lsof -ti tcp:$(FRONT_PORT) || echo not running)"

logs:
	@echo "Tailing logs (Ctrl+C to exit)"
	@tail -n 50 -f $(LOG_DIR)/backend.log $(LOG_DIR)/frontend.log



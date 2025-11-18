.PHONY: dev backend frontend install typegen stop contract-diff frontend-typecheck contract-ci
.ONESHELL:

BACK_HOST=localhost
BACK_PORT=8000
FRONT_PORT=3000
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
	psql "$$DATABASE_URL" -f database/seed.sql

typegen:
	cd frontend && npm run typegen

backend:
	LM_DATABASE_URL=$(DB_URL) $(PYTHON) -m uvicorn app.main:app --app-dir backend --reload --host $(BACK_HOST) --port $(BACK_PORT)

frontend:
	cd frontend && PORT=$(FRONT_PORT) NEXT_PUBLIC_API_BASE_URL=http://$(BACK_HOST):$(BACK_PORT) npm run dev

## Contract checks (OpenAPI as source of truth)
spec-generate:
	# Generate OpenAPI JSON spec from running FastAPI instance
	curl -s http://$(BACK_HOST):$(BACK_PORT)/openapi.json | python -m json.tool > openapi/schema.json
	@echo "Generated openapi/schema.json from FastAPI at http://$(BACK_HOST):$(BACK_PORT)"

spec-sync:
	# Sync openapi/schema.yml to match the running FastAPI (store JSON in .yml which is valid YAML)
	set -e; \
	curl -s http://$(BACK_HOST):$(BACK_PORT)/openapi.json | python -m json.tool > openapi/schema.yml; \
	echo "Synced openapi/schema.yml from FastAPI at http://$(BACK_HOST):$(BACK_PORT)"

contract-diff:
	# Compare local spec vs live FastAPI spec; fail on breaking changes
	set -e; \
	curl -s http://$(BACK_HOST):$(BACK_PORT)/openapi.json > openapi/live.json; \
	npx -y @pb33f/openapi-changes@latest summary openapi/schema.yml openapi/live.json --error-on-diff --no-color

contract-diff-lenient:
	# Normalize schemas to ignore casing, string formats, and required ids; then diff
	set -e; \
	python3 scripts/normalize-openapi.py openapi/schema.yml openapi/schema.norm.json; \
	python3 scripts/normalize-openapi.py openapi/live.json openapi/live.norm.json; \
	npx -y @pb33f/openapi-changes@latest summary openapi/schema.norm.json openapi/live.norm.json --error-on-diff --no-color

frontend-typecheck:
	# Regenerate TS types from OpenAPI and build the app (type-checks contract usage)
	set -e; \
	cd frontend && npm run typegen && npm run build

contract-ci: contract-diff frontend-typecheck
	@echo "Contract checks passed (diff + frontend typecheck)"

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



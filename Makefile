UV            := uv

STLITE_VER    := 0.86.0
STLITE_CSS    := https://cdn.jsdelivr.net/npm/@stlite/browser@$(strip $(STLITE_VER))/build/stlite.css
STLITE_JS     := https://cdn.jsdelivr.net/npm/@stlite/browser@$(strip $(STLITE_VER))/build/stlite.js
APP_PY        := app.py
BUILD_DIR     := build
INDEX_HTML    := $(BUILD_DIR)/index.html

.DEFAULT_GOAL := help

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*?## "};{printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'


.PHONY: setup
setup: install build-html
	@echo ""
	@echo " EpiCON is ready."
	@echo "   • Dev server (normal Streamlit): make dev"
	@echo "   • Serve stlite build locally:    make serve"


.PHONY: install
install:        ## Install Python dependencies with uv
	$(UV) sync


.PHONY: build-html
build-html: $(INDEX_HTML)       ## Generate build/index.html (stlite WASM entry point)

$(INDEX_HTML): $(APP_PY) pyproject.toml | $(BUILD_DIR)
	@echo "→ Generating $(INDEX_HTML) (stlite v$(STLITE_VER))"
	$(UV) run python scripts/build_index.py \
	  --app      $(APP_PY) \
	  --out      $(INDEX_HTML) \
	  --css      $(STLITE_CSS) \
	  --js       $(STLITE_JS) \
	  --title    "EpiCON Cost Calculator"
	@echo "→ Copying static assets into $(BUILD_DIR)/"
	@cp -r utils      $(BUILD_DIR)/utils
	@cp -r config     $(BUILD_DIR)/config
	@cp -r styles     $(BUILD_DIR)/styles      2>/dev/null || true
	@cp -r models     $(BUILD_DIR)/models      2>/dev/null || true
	@cp -r selected   $(BUILD_DIR)/selected    2>/dev/null || true
	@cp -r examples   $(BUILD_DIR)/examples    2>/dev/null || true
	@echo "→ Build artefacts written to $(BUILD_DIR)/"

$(BUILD_DIR):
	mkdir -p $@

.PHONY: dev
dev:
	$(UV) run streamlit run $(APP_PY)

.PHONY: serve
serve: build-html       ## Serve the stlite static build on http://localhost:8000
	@echo "→ Serving stlite build at http://localhost:8000  (Ctrl-C to stop)"
	$(UV) run python -m http.server 8000 --directory $(BUILD_DIR)


.PHONY: lint
lint:           ## Run ruff linter
	$(UV) run ruff check .

.PHONY: typecheck
typecheck:      ## Run mypy type checker
	$(UV) run mypy utils

.PHONY: test
test:           ## Run pytest with coverage
	$(UV) run pytest

.PHONY: check
check: lint typecheck test      ## Run all quality checks (lint + types + tests)


.PHONY: clean
clean:          ## Remove build artefacts
	rm -rf $(BUILD_DIR) .mypy_cache .ruff_cache .pytest_cache __pycache__

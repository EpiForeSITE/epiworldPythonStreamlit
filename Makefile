UV ?= uv

STLITE_VER ?= 0.86.0
PORT ?= 8000

STLITE_CSS := https://cdn.jsdelivr.net/npm/@stlite/browser@$(strip $(STLITE_VER))/build/stlite.css
STLITE_JS := https://cdn.jsdelivr.net/npm/@stlite/browser@$(strip $(STLITE_VER))/build/stlite.js
APP_PY := app.py
SOURCE := src/epicc
BUILD_DIR := build
INDEX_HTML := $(BUILD_DIR)/index.html

STLITE_INPUTS := $(APP_PY) pyproject.toml scripts/build_index.py \
    $(shell find models utils config styles selected examples -type f 2>/dev/null)

.DEFAULT_GOAL := help

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: install build-html ## Install dependencies and build the stlite app

.PHONY: install
install: ## Install Python dependencies with uv
	$(UV) sync

.PHONY: build-html
build-html: $(INDEX_HTML) ## Generate build/index.html (stlite WASM entry point)

$(INDEX_HTML): $(STLITE_INPUTS)
	@mkdir -p $(BUILD_DIR)
	@echo "Generating $(INDEX_HTML) (stlite v$(STLITE_VER))"
	$(UV) run python scripts/build_index.py \
		-app $(APP_PY) \
		--out $(INDEX_HTML) \
		--css $(STLITE_CSS) \
		--js $(STLITE_JS) \
		--title "EpiCON Cost Calculator"
	@echo "Copying static assets into $(BUILD_DIR)/"
	@for dir in utils config styles models selected examples; do \
		if [ -d "$$dir" ]; then cp -r "$$dir" "$(BUILD_DIR)/$$dir"; fi; \
	done
	@echo "Build artifacts written to $(BUILD_DIR)/"

.PHONY: dev
dev: ## Run normal Streamlit locally
	$(UV) run streamlit run $(APP_PY)

.PHONY: serve
serve: build-html ## Serve the stlite static build
	@echo "Serving stlite build at http://localhost:$(PORT) (Ctrl-C to stop)"
	$(UV) run python -m http.server $(PORT) --directory $(BUILD_DIR)

.PHONY: stlite
stlite: setup serve ## Install, build, and serve the stlite app

.PHONY: lint
lint: ## Run ruff linter
	$(UV) tool run ruff check $(SOURCE)

.PHONY: typecheck
typecheck: ## Run mypy type checker
	$(UV) tool run mypy $(SOURCE)

.PHONY: test
test: ## Run pytest
	$(UV) run pytest

.PHONY: check
check: lint typecheck test ## Run all quality checks

.PHONY: clean
clean: ## Remove build artifacts
	rm -rf $(BUILD_DIR) .mypy_cache .ruff_cache .pytest_cache __pycache__

.PHONY: help install ingest generate polish status clear test
.PHONY: debug-ingest debug-generate debug-polish

help:
	@echo ============================================
	@echo  AI Content Pipeline - Commands
	@echo ============================================
	@echo ""
	@echo "  make install           install deps"
	@echo "  make ingest ARGS=...   audio -> knowledge base"
	@echo "  make generate ARGS=... topic -> script"
	@echo "  make polish ARGS=...   polish a script"
	@echo "  make status            view knowledge base"
	@echo "  make clear ARGS=...    clear knowledge base"
	@echo "  make nuke              clear ALL data"
	@echo "  make test              run tests"
	@echo ""
	@echo "  Debug mode (detailed logs):"
	@echo "  make debug-ingest ARGS='-i test.mp3'"
	@echo "  make debug-generate ARGS='-t AI_topic'"
	@echo ""
	@echo "  Examples:"
	@echo "    make ingest ARGS=-i test.mp3"
	@echo "    make generate ARGS=-t AI_topic"
	@echo "    make polish ARGS='-i ./outputs/scripts/创业_20260501_170401.md -f xxx'"
	@echo "    make clear ARGS=--confirm"
	@echo "    make nuke"

install:
	uv sync

ingest:
	uv run python main.py ingest $(ARGS)

generate:
	uv run python main.py generate $(ARGS)

polish:
	uv run python main.py polish $(ARGS)

status:
	uv run python main.py status

clear:
	uv run python main.py clear $(ARGS)

nuke:
	uv run python main.py nuke --confirm

test:
	uv run pytest tests/ -v

test-llm:
	uv run python tests/test_llm_connectivity.py

# Debug targets
debug-ingest:
	uv run python main.py --debug ingest $(ARGS)

debug-generate:
	uv run python main.py --debug generate $(ARGS)

debug-polish:
	uv run python main.py --debug polish $(ARGS)

# AI Content Pipeline
# 用法: make <target> ARGS='...'

help:
	@if [ -z "$(CMD)" ]; then \
		echo "============================================"; \
		echo " AI Content Pipeline"; \
		echo "============================================"; \
		echo ""; \
		echo "  Commands:"; \
		echo "    make ingest      audio -> knowledge base"; \
		echo "    make generate    topic -> script"; \
		echo "    make polish      polish script"; \
		echo "    make produce     script -> video"; \
		echo "    make remotion    script -> Remotion diagram video"; \
		echo "    make kinetic     script -> kinetic text video"; \
			echo "    make remotion    (image_* 模板会自动配图)"; \
		echo "    make review      review generated mp4"; \
		echo "    make status      view knowledge base"; \
		echo "    make clear       clear knowledge base"; \
		echo "    make nuke        clear ALL data"; \
	echo "    make tweet       generate image-text tweet"; \
	echo "    make serve       start REST API server"; \
	echo "    make export      export knowledge base to Obsidian"; \
		echo "    make test        run tests"; \
		echo "    make preview     open Remotion Studio"; \
		echo ""; \
		echo "  Usage:"; \
		echo "    make <target> ARGS='...'     run a command"; \
		echo "    make help CMD=<target>       view all params of a command"; \
		echo ""; \
		echo "  Examples:"; \
		echo "    make help CMD=generate"; \
		echo "    make help CMD=remotion"; \
		echo "    make generate ARGS='-t AI'"; \
		echo "    make remotion ARGS='--script outputs/scripts/xxx.md --job-id r1 --tts --force'"; \
		echo "    make kinetic ARGS='--script outputs/scripts/xxx.md --job-id k1 --tts --force'"; \
	else \
		case "$(CMD)" in \
			ingest) uv run python main.py ingest --help ;; \
			generate) uv run python main.py generate --help ;; \
			polish) uv run python main.py polish --help ;; \
			produce) uv run python main.py produce --help ;; \
			remotion|kinetic) uv run python main.py produce-remotion --help ;; \
			review) uv run python main.py review-video --help ;; \
			clear) uv run python main.py clear --help ;; \
			nuke) uv run python main.py nuke --help ;; \
			serve) uv run python main.py serve --help ;; \
			tweet) uv run python main.py tweet --help ;; \
			export) uv run python main.py export-obsidian --help ;; \
			status) uv run python main.py status --help ;; \
			*) echo "Unknown command: $(CMD)"; echo "Available: ingest generate polish produce remotion kinetic tweet export review clear nuke status serve" ;; \
		esac \
	fi

install:
	uv sync

ingest:
	uv run python main.py ingest $(ARGS)

generate:
	uv run python main.py generate $(ARGS)

polish:
	uv run python main.py polish $(ARGS)

produce:
	uv run python main.py produce $(ARGS)

remotion:
	uv run python main.py produce-remotion $(ARGS)

kinetic:
	uv run python main.py produce-remotion --kinetic $(ARGS)

landscape:
	uv run python main.py produce-remotion --orientation landscape $(ARGS)

review:
	uv run python main.py review-video $(ARGS)

seedance:
	uv run python main.py produce-seedance $(ARGS)

serve:
	uv run python main.py serve $(ARGS)

preview:
	@cmd /C "cd remotion && npm run preview"

status:
	uv run python main.py status

clear:
	uv run python main.py clear $(ARGS)

nuke:
	uv run python main.py nuke --confirm

test:
	uv run pytest tests/ -v

test-ssl-style:
	uv run python tests/test_tts_styles.py

tweet:
	uv run python main.py tweet $(ARGS)

export:
	uv run python main.py export-obsidian $(ARGS)

help:
	@cmd /C echo ============================================
	@cmd /C echo  AI Content Pipeline - Commands
	@cmd /C echo ============================================
	@cmd /C echo.
	@cmd /C echo   make install           install deps
	@cmd /C echo   make ingest ARGS=...   audio -^> knowledge base
	@cmd /C echo   make generate ARGS=... topic -^> script
	@cmd /C echo   make polish ARGS=...   polish a script
	@cmd /C echo   make produce ARGS=...  script -^> video
	@cmd /C echo   make produce-remotion ARGS=... script -^> Remotion video
	@cmd /C echo   make remotion-plan ARGS=... generate Remotion input JSON
	@cmd /C echo   make remotion-render JOB=... render existing Remotion job
	@cmd /C echo   make produce-tts JOB=... add TTS and rebuild existing video job
	@cmd /C echo   make produce-step JOB=... STEP=... rerun one produce step
	@cmd /C echo   make status            view knowledge base
	@cmd /C echo   make clear ARGS=...    clear knowledge base
	@cmd /C echo   make nuke              clear ALL data
	@cmd /C echo   make test              run tests
	@cmd /C echo.
	@cmd /C echo   Debug mode (detailed logs):
	@cmd /C echo   make debug-ingest ARGS='-i test.mp3'
	@cmd /C echo   make debug-generate ARGS='-t AI_topic'
	@cmd /C echo   make debug-produce ARGS='--script ./outputs/scripts/demo.md --job-id demo1'
	@cmd /C echo.
	@cmd /C echo   Examples:
	@cmd /C echo     make ingest ARGS=-i test.mp3
	@cmd /C echo     make generate ARGS=-t AI_topic
	@cmd /C echo     make polish ARGS='-i ./outputs/scripts/demo.md -f xxx'
	@cmd /C echo     make produce ARGS='--script ./outputs/scripts/demo.md --job-id demo1 --no-tts'
	@cmd /C echo     make produce-remotion ARGS='--script ./outputs/scripts/demo.md --job-id demo-remotion'
	@cmd /C echo     make remotion-plan ARGS='--script ./outputs/scripts/demo.md --job-id demo-remotion --force'
	@cmd /C echo     make remotion-render JOB=demo-remotion
	@cmd /C echo     make produce-tts JOB=demo1
	@cmd /C echo     make produce-step JOB=demo1 STEP=animation ARGS=--force
	@cmd /C echo     make produce-step JOB=demo1 STEP=clips ARGS=--force
	@cmd /C echo     make produce-step JOB=demo1 STEP=compose ARGS='--tts --force'
	@cmd /C echo     make clear ARGS=--confirm
	@cmd /C echo     make nuke

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

produce-remotion:
	uv run python main.py produce-remotion $(ARGS)

remotion-plan:
	uv run python main.py produce-remotion --step plan $(ARGS)

remotion-render:
	uv run python main.py produce-remotion --job-id $(JOB) --step render $(ARGS)

produce-tts:
	uv run python main.py produce --job-id $(JOB) --step tts --tts --force $(ARGS)
	uv run python main.py produce --job-id $(JOB) --step clips --force $(ARGS)
	uv run python main.py produce --job-id $(JOB) --step compose --tts --force $(ARGS)

produce-step:
	uv run python main.py produce --job-id $(JOB) --step $(STEP) $(ARGS)

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

debug-produce:
	uv run python main.py --debug produce $(ARGS)

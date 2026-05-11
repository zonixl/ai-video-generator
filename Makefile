# AI Video Generator
# Usage / 用法: make <target> ARGS='...'

help:
	@if [ -z "$(CMD)" ]; then \
		echo "============================================"; \
		echo " AI Video Generator"; \
		echo "============================================"; \
		echo ""; \
		echo "  Commands / 命令:"; \
		echo "    make install     install Python dependencies / 安装 Python 依赖"; \
		echo "    make ingest      audio -> knowledge base / 音频摄入知识库"; \
		echo "    make generate    topic -> script / 选题生成文案"; \
		echo "    make polish      polish script / 润色文案"; \
		echo "    make produce     script -> video / 文案生成常规视频"; \
		echo "    make remotion    script -> Remotion video / 文案生成 Remotion 视频"; \
		echo "    make kinetic     script -> kinetic text video / 动态文字视频"; \
		echo "    make landscape   landscape Remotion video / 横屏 Remotion 视频"; \
		echo "    make hyperframes script -> HyperFrames tech video / 科技感视频"; \
		echo "    make seedance    image/video generation workflow / 图生视频流程"; \
		echo "    make tweet       generate image-text tweet / 生成图文"; \
		echo "    make review      review generated mp4 / 审查视频"; \
		echo "    make serve       start REST API server / 启动后端"; \
		echo "    make preview     open Remotion Studio / 打开 Remotion 预览"; \
		echo "    make status      view knowledge base / 查看知识库状态"; \
		echo "    make export      export knowledge base to Obsidian / 导出知识库"; \
		echo "    make clear       clear knowledge base / 清空知识库"; \
		echo "    make nuke        clear ALL local data / 清空全部本地数据"; \
		echo "    make test        run local tests / 运行本地测试"; \
		echo ""; \
		echo "  Usage / 用法:"; \
		echo "    make <target> ARGS='...'     run a command / 运行命令"; \
		echo "    make help CMD=<target>       view params / 查看参数"; \
		echo ""; \
		echo "  Examples / 示例:"; \
		echo "    make help CMD=generate"; \
		echo "    make help CMD=remotion"; \
		echo "    make generate ARGS='--topic AI'"; \
		echo "    make remotion ARGS='--script outputs/scripts/demo.md --title Demo --template sketch_course --force'"; \
		echo "    make hyperframes ARGS='--script outputs/hf_demo.txt --title Demo --duration 10 --ratio 9:16 --no-render'"; \
	else \
		case "$(CMD)" in \
			ingest) uv run python main.py ingest --help ;; \
			generate) uv run python main.py generate --help ;; \
			polish) uv run python main.py polish --help ;; \
			produce) uv run python main.py produce --help ;; \
			remotion|kinetic|landscape) uv run python main.py produce-remotion --help ;; \
			review) uv run python main.py review-video --help ;; \
			clear) uv run python main.py clear --help ;; \
			nuke) uv run python main.py nuke --help ;; \
			serve) uv run python main.py serve --help ;; \
			tweet) uv run python main.py tweet --help ;; \
			export) uv run python main.py export-obsidian --help ;; \
			hyperframes) uv run python main.py produce-hyperframes --help ;; \
			seedance) uv run python main.py produce-seedance --help ;; \
			status) uv run python main.py status --help ;; \
			*) echo "Unknown command: $(CMD)"; echo "Available: ingest generate polish produce remotion kinetic landscape hyperframes seedance tweet export review clear nuke status serve" ;; \
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

hyperframes:
	uv run python main.py produce-hyperframes $(ARGS)

export:
	uv run python main.py export-obsidian $(ARGS)

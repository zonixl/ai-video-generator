"""CLI 入口：AI内容生产系统。"""

import os
# 禁止 HuggingFace Hub 网络请求，只使用本地缓存
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Settings
from utils.logger import setup_logging
from core.stt import SpeechToText
from core.llm import ModelManager
from core.embedder import Embedder
from core.vectordb import VectorStore
from core.retriever import Retriever
from pipeline.ingest import IngestPipeline
from pipeline.generate import GeneratePipeline
from pipeline.produce import ProducePipeline

logger = logging.getLogger("main")


def build_model_manager(cfg: Settings) -> ModelManager:
    logger.debug("Building ModelManager...")
    return ModelManager(
        providers_cfg=cfg.models_providers,
        instances_cfg=cfg.models_instances,
    )


def build_ingest_pipeline(cfg: Settings) -> IngestPipeline:
    model_mgr = build_model_manager(cfg)
    stt = SpeechToText(
        model_size=cfg.stt_model_size,
        device=cfg.stt_device,
        compute_type=cfg.stt_compute_type,
        language=cfg.stt_language,
    )
    embedder = Embedder(
        model_name=cfg.embedding_model_name,
        device=cfg.embedding_device,
        normalize=cfg.embedding_normalize,
    )
    vs = VectorStore(
        persist_dir=cfg.vectordb_persist_dir,
        collection_name=cfg.vectordb_collection_name,
        embedder=embedder,
    )
    return IngestPipeline(stt, embedder, vs, model_mgr, cfg)


def build_generate_pipeline(cfg: Settings) -> GeneratePipeline:
    model_mgr = build_model_manager(cfg)
    embedder = Embedder(
        model_name=cfg.embedding_model_name,
        device=cfg.embedding_device,
        normalize=cfg.embedding_normalize,
    )
    vs = VectorStore(
        persist_dir=cfg.vectordb_persist_dir,
        collection_name=cfg.vectordb_collection_name,
        embedder=embedder,
    )
    retriever = Retriever(
        vector_store=vs,
        embedder=embedder,
        strategy=cfg.retrieval_strategy,
        top_k=cfg.retrieval_top_k,
        mmr_lambda=cfg.retrieval_mmr_lambda,
    )
    return GeneratePipeline(retriever, model_mgr, cfg)


def build_produce_pipeline(cfg: Settings) -> ProducePipeline:
    return ProducePipeline(cfg)


def _process_one(args_tuple: tuple) -> dict:
    """处理单个文件（供线程池调用）。复用同一个 pipeline 实例。"""
    audio_file, pipeline, force = args_tuple
    return pipeline.run(str(audio_file), force=force)


def cmd_ingest(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)

    input_path = Path(args.input)
    if input_path.is_dir():
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from utils.file_utils import is_audio_file

        audio_files = sorted(
            f for f in input_path.rglob("*")
            if f.is_file() and is_audio_file(f) and f.stat().st_size > 10_000
        )
        if not audio_files:
            logger.warning("No audio files found in: %s", input_path)
            return

        workers = max(1, cfg.ingest_parallel_workers)
        logger.info("Batch ingest: %d files, %d workers", len(audio_files), workers)

        pipeline = build_ingest_pipeline(cfg)  # 只建一次，多线程复用

        ok, skip, fail = 0, 0, 0
        futures = {}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            for audio_file in audio_files:
                future = executor.submit(_process_one, (audio_file, pipeline, args.force))
                futures[future] = audio_file

            for future in as_completed(futures):
                audio_file = futures[future]
                try:
                    result = future.result()
                    if result.get("skipped"):
                        skip += 1
                        logger.info("[%s] skipped (duplicate)", audio_file.name)
                    else:
                        ok += 1
                        logger.info("[%s] ok (%d chunks, %d chars)",
                                    audio_file.name, result["chunks"], result["restructured_chars"])
                except Exception as e:
                    fail += 1
                    logger.error("[%s] FAILED: %s", audio_file.name, e)

        logger.info("Batch done: %d ok, %d skipped, %d failed, %d total",
                    ok, skip, fail, len(audio_files))
    else:
        pipeline = build_ingest_pipeline(cfg)
        # 单文件模式
        result = pipeline.run(args.input, force=args.force)
        if result.get("skipped"):
            logger.info("ingest skipped: duplicate file (hash=%s), use --force to re-ingest", result["hash"])
            return
        logger.info("ingest completed: %d chunks, raw=%d chars, restructured=%d chars -> %s",
                    result["chunks"], result["raw_chars"], result["restructured_chars"],
                    result["restructured_path"])


def cmd_generate(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    pipeline = build_generate_pipeline(cfg)
    script = pipeline.run(args.topic, style=args.style or "专业但不枯燥，适合短视频口播")
    logger.info("generate completed: %d chars", len(script))


def cmd_polish(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    pipeline = build_generate_pipeline(cfg)
    polished = pipeline.polish_to_file(args.input, args.feedback)
    logger.info("polish completed: %d chars", len(polished))


def cmd_produce(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    pipeline = build_produce_pipeline(cfg)
    result = pipeline.run(
        args.script,
        output_path=args.output,
        title=args.title,
        style=args.style,
        width=args.width,
        height=args.height,
        fps=args.fps,
        use_tts=args.use_tts,
        reuse_assets=args.reuse_assets,
    )
    logger.info("produce completed: %s", result.video_path)


def cmd_status(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    vs = VectorStore(
        persist_dir=cfg.vectordb_persist_dir,
        collection_name=cfg.vectordb_collection_name,
    )
    model_mgr = build_model_manager(cfg)
    count = vs.count()
    logger.info("knowledge base status: collection=%s count=%d path=%s",
                cfg.vectordb_collection_name, count, cfg.vectordb_persist_dir)
    logger.info("available model instances: %s", model_mgr.list_instances())


def cmd_nuke(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    if not args.confirm:
        logger.warning("nuke requires --confirm flag. This will delete ALL data!")
        return

    import shutil

    # 1. 清空向量库
    vs = VectorStore(
        persist_dir=cfg.vectordb_persist_dir,
        collection_name=cfg.vectordb_collection_name,
    )
    all_data = vs.get_all()
    if all_data.get("ids"):
        vs.delete_by_ids(all_data["ids"])
        logger.info("[1/4] vectordb: deleted %d documents", len(all_data["ids"]))
    else:
        logger.info("[1/4] vectordb: already empty")

    # 2. 清空转写
    t_dir = cfg.output_transcripts_dir
    if t_dir.exists():
        shutil.rmtree(t_dir)
        t_dir.mkdir(parents=True, exist_ok=True)
    logger.info("[2/4] transcripts: cleared")

    # 3. 清空文案
    s_dir = cfg.output_scripts_dir
    if s_dir.exists():
        shutil.rmtree(s_dir)
        s_dir.mkdir(parents=True, exist_ok=True)
    logger.info("[3/4] scripts: cleared")

    # 4. 清空日志（当前进程占用可能删不掉，忽略）
    import logging as _logging
    for handler in _logging.root.handlers[:]:
        if isinstance(handler, _logging.FileHandler):
            handler.close()
            _logging.root.removeHandler(handler)

    log_path = cfg.logging_file
    try:
        if log_path.exists():
            log_path.unlink()
    except PermissionError:
        pass
    log_dir = log_path.parent
    if log_dir.exists():
        for f in log_dir.glob("*.log*"):
            try:
                f.unlink()
            except PermissionError:
                pass
    print("[4/4] logs: cleared")

    logger.info("nuke complete - all data wiped")


def cmd_clear(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    if not args.confirm:
        logger.warning("clear requires --confirm flag")
        return
    vs = VectorStore(
        persist_dir=cfg.vectordb_persist_dir,
        collection_name=cfg.vectordb_collection_name,
    )
    all_data = vs.get_all()
    if all_data.get("ids"):
        vs.delete_by_ids(all_data["ids"])
        logger.info("cleared %d documents", len(all_data["ids"]))
    else:
        logger.info("knowledge base already empty")


def main():
    parser = argparse.ArgumentParser(
        description="AI内容生产系统 - 短视频文案自动生成"
    )
    parser.add_argument("--config", "-c", default=None,
                        help="配置文件路径 (默认: config/config.yaml)")
    parser.add_argument("--debug", action="store_true",
                        help="启用 DEBUG 日志级别")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    p_ingest = subparsers.add_parser("ingest", help="摄入音频到知识库")
    p_ingest.add_argument("--input", "-i", required=True, help="音频文件或文件夹路径")
    p_ingest.add_argument("--force", "-f", action="store_true", help="强制重新摄入（覆盖已有数据）")

    p_gen = subparsers.add_parser("generate", help="根据话题生成文案")
    p_gen.add_argument("--topic", "-t", required=True, help="话题/关键词")
    p_gen.add_argument("--style", "-s", default=None, help="文案风格（可选）")

    p_polish = subparsers.add_parser("polish", help="润色已有文案")
    p_polish.add_argument("--input", "-i", required=True, help="文案文件路径")
    p_polish.add_argument("--feedback", "-f", required=True, help="修改意见")

    p_produce = subparsers.add_parser("produce", help="根据文案生成图片动画视频")
    p_produce.add_argument("--script", "-s", required=True, help="文案 Markdown/TXT 文件路径")
    p_produce.add_argument("--output", "-o", default=None, help="输出 mp4 路径（可选）")
    p_produce.add_argument("--title", default=None, help="视频标题（可选，默认从文案标题提取）")
    p_produce.add_argument("--style", default="clean", help="画面风格描述")
    p_produce.add_argument("--width", type=int, default=None, help="视频宽度，默认读取配置")
    p_produce.add_argument("--height", type=int, default=None, help="视频高度，默认读取配置")
    p_produce.add_argument("--fps", type=int, default=None, help="视频帧率，默认读取配置")
    p_produce.add_argument("--tts", dest="use_tts", action="store_true", help="启用 edge-tts 配音")
    p_produce.add_argument("--no-tts", dest="use_tts", action="store_false", help="禁用配音")
    p_produce.set_defaults(use_tts=False)
    p_produce.add_argument("--reuse-assets", action="store_true", help="复用已存在的图片和片段")

    subparsers.add_parser("status", help="查看知识库状态")

    p_clear = subparsers.add_parser("clear", help="清空知识库")
    p_clear.add_argument("--confirm", action="store_true", help="确认清空")

    p_nuke = subparsers.add_parser("nuke", help="清除所有数据（知识库+转写+文案+日志）")
    p_nuke.add_argument("--confirm", action="store_true", help="确认清除所有数据")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "ingest": cmd_ingest,
        "generate": cmd_generate,
        "polish": cmd_polish,
        "produce": cmd_produce,
        "status": cmd_status,
        "clear": cmd_clear,
        "nuke": cmd_nuke,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

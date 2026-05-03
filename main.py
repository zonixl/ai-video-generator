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
from core.animation_planner import AIAnimationPlanner, RuleBasedAnimationPlanner
from core.image_provider import ArkSeedreamImageProvider, PlaceholderImageProvider
from core.tts import EdgeTTSProvider, MiMoProvider, iFLYTEKProvider
from core.remotion_planner import AIRemotionPlanner, RuleBasedRemotionPlanner
from core.remotion_refiner import RemotionRefiner
from core.remotion_renderer import RemotionRenderer
from core.scene_splitter import AISceneSplitter, RuleBasedSceneSplitter
from core.video_reviewer import VideoReviewer
from core.vision_provider import OpenAICompatibleVisionProvider
from pipeline.ingest import IngestPipeline
from pipeline.generate import GeneratePipeline
from pipeline.produce import ProducePipeline
from pipeline.produce_remotion import ProduceRemotionPipeline

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


def build_tts_provider(cfg: Settings):
    """根据配置创建 TTS Provider。"""
    if cfg.tts_engine == "mimo":
        return MiMoProvider(
            base_url=cfg.tts_mimo_base_url,
            api_key=cfg.tts_mimo_api_key,
            model=cfg.tts_mimo_model,
        )
    if cfg.tts_engine == "iflytek":
        return iFLYTEKProvider(
            host=cfg.tts_iflytek_host,
            app_id=cfg.tts_iflytek_app_id,
            api_key=cfg.tts_iflytek_api_key,
            api_secret=cfg.tts_iflytek_api_secret,
        )
    return EdgeTTSProvider()


def build_produce_pipeline(cfg: Settings) -> ProducePipeline:
    rule_splitter = RuleBasedSceneSplitter(
        min_scene_duration=cfg.video_min_scene_duration,
        max_scene_duration=cfg.video_max_scene_duration,
        chars_per_second=cfg.video_chars_per_second,
    )
    if cfg.video_scene_splitter == "ai":
        splitter = AISceneSplitter(
            build_model_manager(cfg),
            instance_name=cfg.video_scene_planner_instance,
            fallback=rule_splitter,
            min_scene_duration=cfg.video_min_scene_duration,
            max_scene_duration=cfg.video_max_scene_duration,
        )
    else:
        splitter = rule_splitter

    if cfg.image_gen_engine in {"ark-seedream", "seedream"}:
        image_provider = ArkSeedreamImageProvider(
            base_url=cfg.image_gen_base_url,
            api_key=cfg.image_gen_api_key,
            model=cfg.image_gen_model,
            size=cfg.image_gen_size,
            watermark=cfg.image_gen_watermark,
        )
    else:
        image_provider = PlaceholderImageProvider()

    if cfg.video_animation_planner == "ai":
        animation_planner = AIAnimationPlanner(
            build_model_manager(cfg),
            instance_name=cfg.video_animation_planner_instance,
        )
    else:
        animation_planner = RuleBasedAnimationPlanner()
    return ProducePipeline(
        cfg,
        splitter=splitter,
        image_provider=image_provider,
        animation_planner=animation_planner,
        tts_provider=build_tts_provider(cfg),
    )


def build_produce_remotion_pipeline(cfg: Settings, *, render_only: bool = False, refine_enabled: bool = False, kinetic: bool = False) -> ProduceRemotionPipeline:
    rule_planner = RuleBasedRemotionPlanner()
    if cfg.remotion_planner == "ai" and not render_only:
        planner = AIRemotionPlanner(
            build_model_manager(cfg),
            instance_name=cfg.remotion_planner_instance,
            fallback=rule_planner,
        )
    else:
        planner = rule_planner
    renderer = RemotionRenderer(cfg.remotion_project_dir)
    refiner = None
    if refine_enabled:
        vision_provider = OpenAICompatibleVisionProvider.from_model_config(
            cfg.models_providers,
            cfg.models_instances,
            cfg.remotion_reviewer_instance,
        )
        refiner = RemotionRefiner(
            renderer=renderer,
            vision_provider=vision_provider,
            output_remotion_dir=cfg.output_remotion_dir,
            frames_per_scene=cfg.remotion_review_frames_per_scene,
        )
    kinetic_planner = None
    if kinetic:
        from core.kinetic_planner import KineticTextPlanner
        kinetic_planner = KineticTextPlanner(build_model_manager(cfg))
    # Image provider (for image_* templates)
    if cfg.image_gen_engine in {"ark-seedream", "seedream"}:
        image_provider = ArkSeedreamImageProvider(
            base_url=cfg.image_gen_base_url,
            api_key=cfg.image_gen_api_key,
            model=cfg.image_gen_model,
            size=cfg.image_gen_size,
            watermark=cfg.image_gen_watermark,
        )
    else:
        image_provider = PlaceholderImageProvider()
    return ProduceRemotionPipeline(
        cfg,
        planner=planner,
        renderer=renderer,
        refiner=refiner,
        tts_provider=build_tts_provider(cfg),
        kinetic_planner=kinetic_planner,
        image_provider=image_provider,
    )


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
        job_id=args.job_id,
        from_plan=args.from_plan,
        step=args.step,
        force=args.force,
    )
    logger.info("produce completed: %s", result.video_path)


def cmd_produce_remotion(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    refine_enabled = args.refine or args.step == "refine" or cfg.remotion_refine_enabled
    # --template kinetic_text 自动启用 kinetic planner
    kinetic = args.kinetic or args.template == "kinetic_text"
    # --orientation 预设宽高，--width/--height 优先级更高
    width = args.width
    height = args.height
    if args.orientation == "portrait" and not width and not height:
        width, height = 1080, 1920
    elif args.orientation == "landscape" and not width and not height:
        width, height = 1920, 1080
    pipeline = build_produce_remotion_pipeline(cfg, render_only=args.step in {"render", "refine"}, refine_enabled=refine_enabled, kinetic=kinetic)
    result = pipeline.run(
        args.script,
        job_id=args.job_id,
        output_path=args.output,
        title=args.title,
        width=width,
        height=height,
        fps=args.fps,
        step=args.step,
        force=args.force,
        use_tts=args.tts,
        refine=args.refine,
        refine_rounds=args.refine_rounds,
        review_only=args.review_only,
        template=args.template,
    )
    logger.info("produce-remotion completed: %s", result.video_path)


def cmd_review_video(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    instance_name = args.reviewer_instance or cfg.remotion_reviewer_instance
    vision_provider = OpenAICompatibleVisionProvider.from_model_config(
        cfg.models_providers,
        cfg.models_instances,
        instance_name,
    )
    reviewer = VideoReviewer(
        vision_provider=vision_provider,
        output_dir=args.output_dir or cfg.output_video_reviews_dir,
        max_frame_width=args.max_frame_width,
    )
    result = reviewer.review(
        args.video,
        job_id=args.job_id,
        frame_count=args.frames,
    )
    logger.info("review-video completed: %s", result.review_path)
    print(f"review={result.review_path}")


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
    p_produce.add_argument("--script", "-s", default=None, help="文案 Markdown/TXT 文件路径")
    p_produce.add_argument("--output", "-o", default=None, help="输出 mp4 路径（可选）")
    p_produce.add_argument("--title", default=None, help="视频标题（可选，默认从文案标题提取）")
    p_produce.add_argument("--style", default="clean", help="画面风格描述")
    p_produce.add_argument("--width", type=int, default=None, help="视频宽度，默认读取配置")
    p_produce.add_argument("--height", type=int, default=None, help="视频高度，默认读取配置")
    p_produce.add_argument("--fps", type=int, default=None, help="视频帧率，默认读取配置")
    p_produce.add_argument("--job-id", default=None, help="复用或继续某个 produce 任务")
    p_produce.add_argument("--from-plan", default=None, help="从已有 video_plan.json 继续执行")
    p_produce.add_argument(
        "--step",
        choices=("all", "plan", "animation", "tts", "images", "clips", "subtitles", "compose"),
        default="all",
        help="只执行某个阶段，默认 all",
    )
    p_produce.add_argument("--force", action="store_true", help="强制重做当前 step 对应产物")
    p_produce.add_argument("--tts", dest="use_tts", action="store_true", help="启用 edge-tts 配音")
    p_produce.add_argument("--no-tts", dest="use_tts", action="store_false", help="禁用配音")
    p_produce.set_defaults(use_tts=False)
    p_produce.add_argument("--reuse-assets", action="store_true", help="复用已存在的图片和片段")

    p_remotion = subparsers.add_parser("produce-remotion", help="根据文案生成 Remotion 图示视频")
    p_remotion.add_argument("--script", "-s", default=None, help="文案 Markdown/TXT 文件路径")
    p_remotion.add_argument("--job-id", default=None, help="Remotion 任务 ID")
    p_remotion.add_argument("--output", "-o", default=None, help="输出 mp4 路径（可选）")
    p_remotion.add_argument("--title", default=None, help="视频标题（可选）")
    p_remotion.add_argument("--width", type=int, default=None, help="视频宽度，默认读取配置")
    p_remotion.add_argument("--height", type=int, default=None, help="视频高度，默认读取配置")
    p_remotion.add_argument("--orientation", choices=("portrait", "landscape"), default=None, help="预设画幅：portrait(1080x1920) / landscape(1920x1080)，--width/--height 会覆盖此预设")
    p_remotion.add_argument("--fps", type=int, default=None, help="视频帧率，默认读取配置")
    p_remotion.add_argument(
        "--step",
        choices=("all", "plan", "tts", "kinetic", "image", "refine", "render"),
        default="all",
        help="Remotion 阶段：all / plan / tts / kinetic / image / refine / render",
    )
    p_remotion.add_argument("--force", action="store_true", help="强制重做 Remotion input")
    p_remotion.add_argument("--tts", action="store_true", default=False, help="启用 TTS 语音合成")
    p_remotion.add_argument("--kinetic", action="store_true", default=False, help="启用逐词动态文字模式")
    p_remotion.add_argument("--template", default=None, help="强制指定模板（如 kinetic_text, image_elegant 等），不传则 AI 自行决策")
    p_remotion.add_argument("--refine", action="store_true", help="在 all 流程中启用视觉自迭代")
    p_remotion.add_argument("--refine-rounds", type=int, default=None, help="视觉自迭代最大轮数")
    p_remotion.add_argument("--review-only", action="store_true", help="只输出视觉审查报告，不应用 patch")

    p_review_video = subparsers.add_parser("review-video", help="用多模态模型审查已生成视频")
    p_review_video.add_argument("--video", "-v", required=True, help="待审查 mp4 路径")
    p_review_video.add_argument("--job-id", default=None, help="审查任务 ID，默认取视频文件名")
    p_review_video.add_argument("--frames", type=int, default=7, help="抽取关键帧数量，默认 7")
    p_review_video.add_argument("--max-frame-width", type=int, default=768, help="送审关键帧最大宽度，默认 768")
    p_review_video.add_argument("--output-dir", default=None, help="审查报告输出目录")
    p_review_video.add_argument("--reviewer-instance", default=None, help="覆盖配置中的 reviewer instance")

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
        "produce-remotion": cmd_produce_remotion,
        "review-video": cmd_review_video,
        "status": cmd_status,
        "clear": cmd_clear,
        "nuke": cmd_nuke,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

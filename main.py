"""CLI 鍏ュ彛锛欰I鍐呭鐢熶骇绯荤粺銆?""


import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Settings
from utils.logger import setup_logging

logger = logging.getLogger("main")


def build_model_manager(cfg: Settings):
    from core.llm import ModelManager
    logger.debug("Building ModelManager...")
    return ModelManager(
        providers_cfg=cfg.models_providers,
        instances_cfg=cfg.models_instances,
    )


def build_ingest_pipeline(cfg: Settings):
    from core.stt import SpeechToText
    from core.embedder import Embedder
    from core.vectordb import VectorStore
    from pipeline.ingest import IngestPipeline
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


def build_generate_pipeline(cfg: Settings):
    from core.embedder import Embedder
    from core.vectordb import VectorStore
    from core.retriever import Retriever
    from pipeline.generate import GeneratePipeline
    model_mgr = build_model_manager(cfg)
    retriever = None
    try:
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
    except Exception as exc:
        logger.warning("Knowledge retrieval disabled for generation: %s", exc)
    return GeneratePipeline(retriever, model_mgr, cfg)


def build_tweet_pipeline(cfg: Settings):
    from core.embedder import Embedder
    from core.vectordb import VectorStore
    from core.retriever import Retriever
    from pipeline.tweet import TweetPipeline
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
    image_provider = build_image_provider(cfg)
    return TweetPipeline(retriever, model_mgr, image_provider, cfg)


def build_tts_provider(cfg: Settings):
    """鏍规嵁閰嶇疆鍒涘缓 TTS Provider銆?""
    from core.tts import EdgeTTSProvider, MiMoProvider, iFLYTEKProvider
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


def build_image_provider(cfg: Settings):
    """鏍规嵁閰嶇疆鍒涘缓鍥剧墖鐢熸垚 Provider銆?""
    from core.image_provider import ArkSeedreamImageProvider, GPTImageProvider, PlaceholderImageProvider
    if cfg.image_gen_engine in {"ark-seedream", "seedream"}:
        return ArkSeedreamImageProvider(
            base_url=cfg.image_gen_base_url,
            api_key=cfg.image_gen_api_key,
            model=cfg.image_gen_model,
            size=cfg.image_gen_size,
            watermark=cfg.image_gen_watermark,
        )
    if cfg.image_gen_engine == "gpt-image":
        return GPTImageProvider(
            base_url=cfg.image_gen_base_url,
            api_key=cfg.image_gen_api_key,
            model=cfg.image_gen_model,
            size=cfg.image_gen_size,
            quality=cfg.image_gen_quality,
        )
    return PlaceholderImageProvider()


def build_produce_pipeline(cfg: Settings):
    from core.animation_planner import AIAnimationPlanner, RuleBasedAnimationPlanner
    from core.scene_splitter import AISceneSplitter, RuleBasedSceneSplitter
    from pipeline.produce import ProducePipeline
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

    image_provider = build_image_provider(cfg)

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


def build_produce_remotion_pipeline(cfg: Settings, *, render_only: bool = False, refine_enabled: bool = False, kinetic: bool = False):
    from core.remotion_planner import AIRemotionPlanner, RuleBasedRemotionPlanner
    from core.remotion_refiner import RemotionRefiner
    from core.remotion_renderer import RemotionRenderer
    from core.vision_provider import OpenAICompatibleVisionProvider
    from pipeline.produce_remotion import ProduceRemotionPipeline
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
            output_videos_dir=cfg.output_videos_dir,
            frames_per_scene=cfg.remotion_review_frames_per_scene,
        )
    kinetic_planner = None
    if kinetic:
        from core.kinetic_planner import KineticTextPlanner
        kinetic_planner = KineticTextPlanner(build_model_manager(cfg))
    # Image provider (for image_* templates)
    image_provider = build_image_provider(cfg)
    model_mgr = build_model_manager(cfg)
    return ProduceRemotionPipeline(
        cfg,
        planner=planner,
        renderer=renderer,
        refiner=refiner,
        tts_provider=build_tts_provider(cfg),
        kinetic_planner=kinetic_planner,
        image_provider=image_provider,
        model_manager=model_mgr,
    )


def build_produce_hyperframes_pipeline(cfg: Settings):
    from pipeline.produce_hyperframes import ProduceHyperframesPipeline
    return ProduceHyperframesPipeline(cfg, model_manager=build_model_manager(cfg))


def build_produce_seedance_pipeline(cfg: Settings):
    from core.scene_splitter import AISceneSplitter, RuleBasedSceneSplitter
    from core.video_gen_provider import SeedanceVideoProvider
    from pipeline.produce_seedance import ProduceSeedancePipeline
    # splitter
    rule_splitter = RuleBasedSceneSplitter(
        min_scene_duration=cfg.video_min_scene_duration,
        max_scene_duration=cfg.video_max_scene_duration,
        chars_per_second=cfg.video_chars_per_second,
    )
    model_mgr = build_model_manager(cfg)
    if cfg.video_scene_splitter == "ai":
        splitter = AISceneSplitter(
            model_mgr,
            instance_name=cfg.video_scene_planner_instance,
            fallback=rule_splitter,
            min_scene_duration=cfg.video_min_scene_duration,
            max_scene_duration=cfg.video_max_scene_duration,
        )
    else:
        splitter = rule_splitter

    # image provider
    image_provider = build_image_provider(cfg)

    # video provider (Seedance)
    video_provider = None
    if cfg.video_gen_engine == "seedance":
        api_key = cfg.video_gen_api_key or cfg.image_gen_api_key
        video_provider = SeedanceVideoProvider(
            base_url=cfg.video_gen_base_url,
            api_key=api_key,
            model=cfg.video_gen_model,
            resolution=cfg.video_gen_resolution,
            ratio=cfg.video_gen_ratio,
            duration=cfg.video_gen_duration,
            generate_audio=cfg.video_gen_generate_audio,
            watermark=cfg.video_gen_watermark,
            timeout=cfg.video_gen_timeout,
            poll_interval=cfg.video_gen_poll_interval,
        )

    return ProduceSeedancePipeline(
        cfg,
        splitter=splitter,
        image_provider=image_provider,
        video_provider=video_provider,
        tts_provider=build_tts_provider(cfg),
        model_manager=model_mgr,
    )


def _process_one(args_tuple: tuple) -> dict:
    """澶勭悊鍗曚釜鏂囦欢锛堜緵绾跨▼姹犺皟鐢級銆傚鐢ㄥ悓涓€涓?pipeline 瀹炰緥銆?""
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

        pipeline = build_ingest_pipeline(cfg)  # 鍙缓涓€娆★紝澶氱嚎绋嬪鐢?
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
        # 鍗曟枃浠舵ā寮?        result = pipeline.run(args.input, force=args.force)
        if result.get("skipped"):
            logger.info("ingest skipped: duplicate file (hash=%s), use --force to re-ingest", result["hash"])
            return
        logger.info("ingest completed: %d chunks, raw=%d chars, restructured=%d chars -> %s",
                    result["chunks"], result["raw_chars"], result["restructured_chars"],
                    result["restructured_path"])


def cmd_ingest_text(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    pipeline = build_ingest_pipeline(cfg)

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8")
        source_name = Path(args.input).stem
    elif args.text:
        text = args.text
        source_name = args.name or "direct_input"
    else:
        logger.error("闇€瑕?--text 鎴?--input 鍙傛暟")
        return

    result = pipeline.ingest_text(text, source_name=source_name, force=args.force)
    if result.get("skipped"):
        logger.info("ingest-text skipped: duplicate (hash=%s)", result["hash"])
        return
    logger.info("ingest-text completed: %d chunks, raw=%d chars, restructured=%d chars",
                result["chunks"], result["raw_chars"], result["restructured_chars"])


def cmd_generate(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    pipeline = build_generate_pipeline(cfg)
    script = pipeline.run(args.topic, style=args.style or "涓撲笟浣嗕笉鏋嚗锛岄€傚悎鐭棰戝彛鎾?)
    logger.info("generate completed: %d chars", len(script))


def cmd_polish(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    pipeline = build_generate_pipeline(cfg)
    polished = pipeline.polish_to_file(args.input, args.feedback)
    logger.info("polish completed: %d chars", len(polished))


def cmd_tweet(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    if not args.topic and not args.draft:
        logger.error("蹇呴』鎻愪緵 --topic 鎴?--draft 涔嬩竴")
        return
    pipeline = build_tweet_pipeline(cfg)
    out_path = pipeline.run(
        topic=args.topic,
        draft_path=args.draft,
        feedback=args.feedback or "",
        output_path=args.output,
        no_images=args.no_images,
    )
    logger.info("tweet completed: %s", out_path)
    return {"output_path": out_path}


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
    return result


def cmd_produce_remotion(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    # --tts-mode 杩愯鏃惰鐩栭厤缃?    if getattr(args, 'tts_mode', None):
        cfg._flat["tts_mode"] = args.tts_mode
    refine_enabled = args.refine or args.step == "refine" or cfg.remotion_refine_enabled
    # --template kinetic_text 鑷姩鍚敤 kinetic planner
    kinetic = args.kinetic or args.template == "kinetic_text"
    # --orientation 棰勮瀹介珮锛?-width/--height 浼樺厛绾ф洿楂?    width = args.width
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
    return result


def cmd_produce_hyperframes(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    pipeline = build_produce_hyperframes_pipeline(cfg)
    result = pipeline.run(
        args.script,
        job_id=args.job_id,
        output_path=args.output,
        title=args.title,
        duration=args.duration,
        ratio=args.ratio,
        style=args.style,
        fps=args.fps,
        use_agents_sdk=not args.no_agents_sdk,
        render=not args.no_render,
        preview=args.preview,
    )
    logger.info("produce-hyperframes completed: workspace=%s output=%s rendered=%s", result.workspace_path, result.output_path, result.rendered)
    print(f"job_id={result.job_id}")
    print(f"workspace={result.workspace_path}")
    print(f"output={result.output_path}")
    print(f"rendered={result.rendered}")
    return {"output_path": result.output_path, "workspace_path": result.workspace_path, "rendered": result.rendered}


def cmd_review_video(args):
    from core.vision_provider import OpenAICompatibleVisionProvider
    from core.video_reviewer import VideoReviewer
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


def cmd_produce_seedance(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    pipeline = build_produce_seedance_pipeline(cfg)
    # --tts 闅愬惈 audio_mode=tts
    audio_mode = args.audio_mode
    if args.use_tts and audio_mode == "tts":
        pass  # 鐢ㄦ埛鏄惧紡鎸囧畾 --tts + --audio-mode tts
    elif args.use_tts:
        audio_mode = "tts"
    result = pipeline.run(
        args.script,
        output_path=args.output,
        title=args.title,
        width=args.width,
        height=args.height,
        fps=args.fps,
        job_id=args.job_id,
        step=args.step,
        force=args.force,
        audio_mode=audio_mode,
        use_tts=args.use_tts,
        auto_confirm=args.auto_confirm,
        regenerate=args.regenerate,
        user_images_dir=args.user_images,
    )
    logger.info("produce-seedance completed: %s", result["video_path"])
    return result


def cmd_status(args):
    from core.vectordb import VectorStore
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
    from core.vectordb import VectorStore
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    if not args.confirm:
        logger.warning("nuke requires --confirm flag. This will delete ALL data!")
        return

    import shutil

    # 1. 娓呯┖鍚戦噺搴?    vs = VectorStore(
        persist_dir=cfg.vectordb_persist_dir,
        collection_name=cfg.vectordb_collection_name,
    )
    all_data = vs.get_all()
    if all_data.get("ids"):
        vs.delete_by_ids(all_data["ids"])
        logger.info("[1/4] vectordb: deleted %d documents", len(all_data["ids"]))
    else:
        logger.info("[1/4] vectordb: already empty")

    # 2. 娓呯┖杞啓
    t_dir = cfg.output_transcripts_dir
    if t_dir.exists():
        shutil.rmtree(t_dir)
        t_dir.mkdir(parents=True, exist_ok=True)
    logger.info("[2/4] transcripts: cleared")

    # 3. 娓呯┖鏂囨
    s_dir = cfg.output_scripts_dir
    if s_dir.exists():
        shutil.rmtree(s_dir)
        s_dir.mkdir(parents=True, exist_ok=True)
    logger.info("[3/4] scripts: cleared")

    # 4. 娓呯┖鏃ュ織锛堝綋鍓嶈繘绋嬪崰鐢ㄥ彲鑳藉垹涓嶆帀锛屽拷鐣ワ級
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


def cmd_serve(args):
    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)
    from api.app import start
    logger.info("Starting API server on %s:%d", args.host, args.port)
    start(host=args.host, port=args.port)


def cmd_clear(args):
    from core.vectordb import VectorStore
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


def cmd_export_obsidian(args):
    """瀵煎嚭鐭ヨ瘑搴撳叏閮ㄥ唴瀹逛负 Obsidian 绗旇銆?""
    from datetime import datetime
    from collections import defaultdict
    from core.vectordb import VectorStore

    cfg = Settings(args.config)
    setup_logging(cfg, debug=args.debug)

    vs = VectorStore(
        persist_dir=cfg.vectordb_persist_dir,
        collection_name=cfg.vectordb_collection_name,
    )
    all_data = vs.get_all()
    if not all_data.get("ids"):
        logger.warning("鐭ヨ瘑搴撲负绌猴紝鏃犲唴瀹瑰彲瀵煎嚭")
        return

    output_dir = Path(args.output) if args.output else Path("outputs/obsidian")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 鎸?(source_name, file_hash) 鍒嗙粍
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for i, doc_id in enumerate(all_data["ids"]):
        meta = all_data["metadatas"][i] if all_data["metadatas"] else {}
        text = all_data["documents"][i] if all_data["documents"] else ""
        key = (meta.get("source_name", "unknown"), meta.get("file_hash", ""))
        groups[key].append({
            "chunk_index": meta.get("chunk_index", 0),
            "text": text,
            "meta": meta,
        })

    # 姣忕粍鎸?chunk_index 鎺掑簭骞跺啓鍑?    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    exported = 0
    for (source_name, file_hash), chunks in groups.items():
        chunks.sort(key=lambda c: c["chunk_index"])
        full_text = "\n\n".join(c["text"] for c in chunks)
        sample_meta = chunks[0]["meta"]

        # 鏂囦欢鍚嶏細鍘绘帀鎵╁睍鍚嶏紝鐢?source_name
        stem = Path(source_name).stem
        safe_name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in stem).strip()
        if not safe_name:
            safe_name = "untitled"

        # 閬垮厤鍚屽悕瑕嗙洊
        out_path = output_dir / f"{safe_name}.md"
        counter = 1
        while out_path.exists():
            out_path = output_dir / f"{safe_name}_{counter}.md"
            counter += 1

        frontmatter = (
            f"---\n"
            f"source: \"{source_name}\"\n"
            f"hash: \"{file_hash}\"\n"
            f"chunks: {len(chunks)}\n"
            f"restructured: {sample_meta.get('restructured', False)}\n"
            f"raw_chars: {sample_meta.get('raw_chars', 0)}\n"
            f"restructured_chars: {sample_meta.get('restructured_chars', 0)}\n"
            f"exported: \"{now}\"\n"
            f"tags:\n  - 鐭ヨ瘑搴揬n"
            f"---\n\n"
        )
        out_path.write_text(frontmatter + full_text, encoding="utf-8")
        exported += 1
        logger.info("瀵煎嚭: %s (%d chunks, %d chars)", out_path.name, len(chunks), len(full_text))

    logger.info("瀵煎嚭瀹屾垚: %d 绡囩瑪璁?-> %s", exported, output_dir)


def main():
    parser = argparse.ArgumentParser(
        description="AI鍐呭鐢熶骇绯荤粺 - 鐭棰戞枃妗堣嚜鍔ㄧ敓鎴?
    )
    parser.add_argument("--config", "-c", default=None,
                        help="閰嶇疆鏂囦欢璺緞 (榛樿: config/config.yaml)")
    parser.add_argument("--debug", action="store_true",
                        help="鍚敤 DEBUG 鏃ュ織绾у埆")

    subparsers = parser.add_subparsers(dest="command", help="鍙敤鍛戒护")

    p_ingest = subparsers.add_parser("ingest", help="鎽勫叆闊抽鍒扮煡璇嗗簱")
    p_ingest.add_argument("--input", "-i", required=True, help="闊抽鏂囦欢鎴栨枃浠跺す璺緞")
    p_ingest.add_argument("--force", "-f", action="store_true", help="寮哄埗閲嶆柊鎽勫叆锛堣鐩栧凡鏈夋暟鎹級")

    p_ingest_text = subparsers.add_parser("ingest-text", help="鐩存帴鏂囨湰鎽勫叆鐭ヨ瘑搴?)
    p_ingest_text.add_argument("--text", "-t", default=None, help="鐩存帴杈撳叆鏂囨湰鍐呭")
    p_ingest_text.add_argument("--input", "-i", default=None, help="鏂囨湰鏂囦欢璺緞")
    p_ingest_text.add_argument("--name", "-n", default=None, help="鏉ユ簮鍚嶇О锛堥粯璁?direct_input锛?)
    p_ingest_text.add_argument("--force", "-f", action="store_true", help="寮哄埗閲嶆柊鎽勫叆")

    p_gen = subparsers.add_parser("generate", help="鏍规嵁璇濋鐢熸垚鏂囨")
    p_gen.add_argument("--topic", "-t", required=True, help="璇濋/鍏抽敭璇?)
    p_gen.add_argument("--style", "-s", default=None, help="鏂囨椋庢牸锛堝彲閫夛級")

    p_polish = subparsers.add_parser("polish", help="娑﹁壊宸叉湁鏂囨")
    p_polish.add_argument("--input", "-i", required=True, help="鏂囨鏂囦欢璺緞")
    p_polish.add_argument("--feedback", "-f", required=True, help="淇敼鎰忚")

    p_produce = subparsers.add_parser("produce", help="鏍规嵁鏂囨鐢熸垚鍥剧墖鍔ㄧ敾瑙嗛")
    p_produce.add_argument("--script", "-s", default=None, help="鏂囨 Markdown/TXT 鏂囦欢璺緞")
    p_produce.add_argument("--output", "-o", default=None, help="杈撳嚭 mp4 璺緞锛堝彲閫夛級")
    p_produce.add_argument("--title", default=None, help="瑙嗛鏍囬锛堝彲閫夛紝榛樿浠庢枃妗堟爣棰樻彁鍙栵級")
    p_produce.add_argument("--style", default="clean", help="鐢婚潰椋庢牸鎻忚堪")
    p_produce.add_argument("--width", type=int, default=None, help="瑙嗛瀹藉害锛岄粯璁よ鍙栭厤缃?)
    p_produce.add_argument("--height", type=int, default=None, help="瑙嗛楂樺害锛岄粯璁よ鍙栭厤缃?)
    p_produce.add_argument("--fps", type=int, default=None, help="瑙嗛甯х巼锛岄粯璁よ鍙栭厤缃?)
    p_produce.add_argument("--job-id", default=None, help="澶嶇敤鎴栫户缁煇涓?produce 浠诲姟")
    p_produce.add_argument("--from-plan", default=None, help="浠庡凡鏈?video_plan.json 缁х画鎵ц")
    p_produce.add_argument(
        "--step",
        choices=("all", "plan", "animation", "tts", "images", "clips", "subtitles", "compose"),
        default="all",
        help="鍙墽琛屾煇涓樁娈碉紝榛樿 all",
    )
    p_produce.add_argument("--force", action="store_true", help="寮哄埗閲嶅仛褰撳墠 step 瀵瑰簲浜х墿")
    p_produce.add_argument("--tts", dest="use_tts", action="store_true", help="鍚敤 edge-tts 閰嶉煶")
    p_produce.add_argument("--no-tts", dest="use_tts", action="store_false", help="绂佺敤閰嶉煶")
    p_produce.set_defaults(use_tts=False)
    p_produce.add_argument("--reuse-assets", action="store_true", help="澶嶇敤宸插瓨鍦ㄧ殑鍥剧墖鍜岀墖娈?)

    p_remotion = subparsers.add_parser("produce-remotion", help="鏍规嵁鏂囨鐢熸垚 Remotion 鍥剧ず瑙嗛")
    p_remotion.add_argument("--script", "-s", default=None, help="鏂囨 Markdown/TXT 鏂囦欢璺緞")
    p_remotion.add_argument("--job-id", default=None, help="Remotion 浠诲姟 ID")
    p_remotion.add_argument("--output", "-o", default=None, help="杈撳嚭 mp4 璺緞锛堝彲閫夛級")
    p_remotion.add_argument("--title", default=None, help="瑙嗛鏍囬锛堝彲閫夛級")
    p_remotion.add_argument("--width", type=int, default=None, help="瑙嗛瀹藉害锛岄粯璁よ鍙栭厤缃?)
    p_remotion.add_argument("--height", type=int, default=None, help="瑙嗛楂樺害锛岄粯璁よ鍙栭厤缃?)
    p_remotion.add_argument("--orientation", choices=("portrait", "landscape"), default=None, help="棰勮鐢诲箙锛歱ortrait(1080x1920) / landscape(1920x1080)锛?-width/--height 浼氳鐩栨棰勮")
    p_remotion.add_argument("--fps", type=int, default=None, help="瑙嗛甯х巼锛岄粯璁よ鍙栭厤缃?)
    p_remotion.add_argument(
        "--step",
        choices=("all", "plan", "tts", "kinetic", "image", "refine", "render"),
        default="all",
        help="Remotion 闃舵锛歛ll / plan / tts / kinetic / image / refine / render",
    )
    p_remotion.add_argument("--force", action="store_true", help="寮哄埗閲嶅仛 Remotion input")
    p_remotion.add_argument("--tts", action="store_true", default=False, help="鍚敤 TTS 璇煶鍚堟垚")
    p_remotion.add_argument("--tts-mode", choices=("per_scene", "whole_article"), default=None, help="TTS 妯″紡: per_scene=閫愬満鏅儏缁?榛樿), whole_article=鏁寸瘒缁熶竴椋庢牸")
    p_remotion.add_argument("--kinetic", action="store_true", default=False, help="鍚敤閫愯瘝鍔ㄦ€佹枃瀛楁ā寮?)
    p_remotion.add_argument("--template", default=None, help="寮哄埗鎸囧畾妯℃澘锛堝 kinetic_text, image_elegant 绛夛級锛屼笉浼犲垯 AI 鑷鍐崇瓥")
    p_remotion.add_argument("--refine", action="store_true", help="鍦?all 娴佺▼涓惎鐢ㄨ瑙夎嚜杩唬")
    p_remotion.add_argument("--refine-rounds", type=int, default=None, help="瑙嗚鑷凯浠ｆ渶澶ц疆鏁?)
    p_remotion.add_argument("--review-only", action="store_true", help="鍙緭鍑鸿瑙夊鏌ユ姤鍛婏紝涓嶅簲鐢?patch")

    p_hyperframes = subparsers.add_parser("produce-hyperframes", help="generate a safe HyperFrames technology-style video")
    p_hyperframes.add_argument("--script", "-s", required=True, help="script Markdown/TXT path")
    p_hyperframes.add_argument("--job-id", default=None, help="HyperFrames job id")
    p_hyperframes.add_argument("--output", "-o", default=None, help="output mp4 path")
    p_hyperframes.add_argument("--title", default=None, help="video title")
    p_hyperframes.add_argument("--duration", type=int, default=15, help="video duration, 5-30 seconds")
    p_hyperframes.add_argument("--ratio", choices=("9:16", "16:9", "1:1"), default="9:16", help="video ratio")
    p_hyperframes.add_argument("--style", choices=("tech_hud", "data_stream", "glassmorphism", "cyber_grid"), default="tech_hud", help="visual style")
    p_hyperframes.add_argument("--fps", type=int, default=None, help="video fps")
    p_hyperframes.add_argument("--preview", action="store_true", help="render a preview still before video render")
    p_hyperframes.add_argument("--no-render", action="store_true", help="only generate sandbox files, skip HyperFrames CLI render")
    p_hyperframes.add_argument("--no-agents-sdk", action="store_true", help="skip OpenAI Agents SDK and use the local fallback generator")

    p_seedance = subparsers.add_parser("produce-seedance", help="Seedance 鍥剧敓瑙嗛")
    p_seedance.add_argument("--script", "-s", default=None, help="鏂囨 Markdown/TXT 鏂囦欢璺緞")
    p_seedance.add_argument("--job-id", default=None, help="浠诲姟 ID")
    p_seedance.add_argument("--output", "-o", default=None, help="杈撳嚭 mp4 璺緞")
    p_seedance.add_argument("--title", default=None, help="瑙嗛鏍囬")
    p_seedance.add_argument("--width", type=int, default=None, help="瑙嗛瀹藉害")
    p_seedance.add_argument("--height", type=int, default=None, help="瑙嗛楂樺害")
    p_seedance.add_argument("--fps", type=int, default=None, help="瑙嗛甯х巼")
    p_seedance.add_argument(
        "--step",
        choices=("all", "plan", "images", "videos", "subtitles", "compose", "unify"),
        default="all",
        help="鎵ц闃舵锛歛ll / plan / images / videos / subtitles / compose / unify",
    )
    p_seedance.add_argument("--force", action="store_true", help="寮哄埗閲嶅仛")
    p_seedance.add_argument(
        "--audio-mode",
        choices=("seedance-audio", "tts", "none"),
        default="tts",
        help="闊抽妯″紡锛歴eedance-audio(S鑷甫闊抽) / tts(閰嶉煶鍚堟垚) / none(鏃犻煶棰?",
    )
    p_seedance.add_argument("--tts", dest="use_tts", action="store_true", help="鍚敤 TTS 閰嶉煶")
    p_seedance.add_argument("--no-tts", dest="use_tts", action="store_false")
    p_seedance.set_defaults(use_tts=False)
    p_seedance.add_argument("--auto-confirm", action="store_true", help="鑷姩鐢熸垚锛岃烦杩囩‘璁?)
    p_seedance.add_argument("--regenerate", type=int, default=None, help="閲嶆柊鐢熸垚鎸囧畾 scene 鐨勫浘鐗?)
    p_seedance.add_argument("--user-images", default=None, help="鐢ㄦ埛鑷畾涔夊浘鐗囩洰褰?)

    p_review_video = subparsers.add_parser("review-video", help="鐢ㄥ妯℃€佹ā鍨嬪鏌ュ凡鐢熸垚瑙嗛")
    p_review_video.add_argument("--video", "-v", required=True, help="寰呭鏌?mp4 璺緞")
    p_review_video.add_argument("--job-id", default=None, help="瀹℃煡浠诲姟 ID锛岄粯璁ゅ彇瑙嗛鏂囦欢鍚?)
    p_review_video.add_argument("--frames", type=int, default=7, help="鎶藉彇鍏抽敭甯ф暟閲忥紝榛樿 7")
    p_review_video.add_argument("--max-frame-width", type=int, default=768, help="閫佸鍏抽敭甯ф渶澶у搴︼紝榛樿 768")
    p_review_video.add_argument("--output-dir", default=None, help="瀹℃煡鎶ュ憡杈撳嚭鐩綍")
    p_review_video.add_argument("--reviewer-instance", default=None, help="瑕嗙洊閰嶇疆涓殑 reviewer instance")

    subparsers.add_parser("status", help="鏌ョ湅鐭ヨ瘑搴撶姸鎬?)

    p_clear = subparsers.add_parser("clear", help="娓呯┖鐭ヨ瘑搴?)
    p_clear.add_argument("--confirm", action="store_true", help="纭娓呯┖")

    p_nuke = subparsers.add_parser("nuke", help="娓呴櫎鎵€鏈夋暟鎹紙鐭ヨ瘑搴?杞啓+鏂囨+鏃ュ織锛?)
    p_nuke.add_argument("--confirm", action="store_true", help="纭娓呴櫎鎵€鏈夋暟鎹?)

    p_serve = subparsers.add_parser("serve", help="鍚姩 REST API 鏈嶅姟")
    p_serve.add_argument("--host", default="0.0.0.0", help="鐩戝惉鍦板潃 (榛樿: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="鐩戝惉绔彛 (榛樿: 8000)")

    p_tweet = subparsers.add_parser("tweet", help="鐢熸垚鍥炬枃鎺ㄦ枃")
    p_tweet.add_argument("--topic", "-t", default=None, help="璇濋/鍏抽敭璇嶏紙涓?--draft 浜岄€変竴锛?)
    p_tweet.add_argument("--draft", "-d", default=None, help="鏂囩珷鍒濈鏂囦欢璺緞锛堜笌 --topic 浜岄€変竴锛?)
    p_tweet.add_argument("--feedback", "-f", default=None, help="娑﹁壊鎰忚锛堝彲閫夛級")
    p_tweet.add_argument("--output", "-o", default=None, help="杈撳嚭 MD 璺緞锛堝彲閫夛級")
    p_tweet.add_argument("--no-images", action="store_true", help="鍙敓鎴愭枃瀛楋紝涓嶇敓鎴愰厤鍥?)

    p_export = subparsers.add_parser("export-obsidian", help="瀵煎嚭鐭ヨ瘑搴撲负 Obsidian 绗旇")
    p_export.add_argument("--output", "-o", default=None, help="杈撳嚭鐩綍锛堥粯璁?outputs/obsidian锛?)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    commands = {
        "ingest": cmd_ingest,
        "ingest-text": cmd_ingest_text,
        "generate": cmd_generate,
        "polish": cmd_polish,
        "tweet": cmd_tweet,
        "produce": cmd_produce,
        "produce-remotion": cmd_produce_remotion,
        "produce-hyperframes": cmd_produce_hyperframes,
        "produce-seedance": cmd_produce_seedance,
        "review-video": cmd_review_video,
        "status": cmd_status,
        "clear": cmd_clear,
        "nuke": cmd_nuke,
        "serve": cmd_serve,
        "export-obsidian": cmd_export_obsidian,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

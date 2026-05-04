"""Seedance 视频生产流程：文案 → 分镜 → 参考图 → 视频 → 拼接。"""

from __future__ import annotations

import logging
import subprocess
import time
from pathlib import Path

from core.image_provider import ImageProvider, PlaceholderImageProvider
from core.scene_splitter import RuleBasedSceneSplitter
from core.schema import AudioAsset, Scene, VideoPlan, to_dict, video_plan_from_dict
from core.tts import EdgeTTSProvider, TTSProvider
from core.video_gen_provider import SeedanceVideoProvider
from utils.file_utils import read_json, read_text, write_json
from utils.media_utils import make_job_id, scene_filename
from utils.subtitle_utils import write_srt

logger = logging.getLogger(__name__)

SEEDANCE_STEPS = ("all", "plan", "images", "videos", "subtitles", "compose", "unify")


class ProduceSeedancePipeline:
    """文案 → 分镜 → 参考图(交互确认) → Seedance 视频 → 拼接。"""

    def __init__(
        self,
        config,
        *,
        splitter=None,
        image_provider: ImageProvider | None = None,
        video_provider: SeedanceVideoProvider | None = None,
        tts_provider: TTSProvider | None = None,
        model_manager=None,
    ):
        self._cfg = config
        self._splitter = splitter or RuleBasedSceneSplitter(
            min_scene_duration=getattr(config, "video_min_scene_duration", 5.0),
            max_scene_duration=getattr(config, "video_max_scene_duration", 8.0),
            chars_per_second=getattr(config, "video_chars_per_second", 4.5),
        )
        self._image_provider = image_provider or PlaceholderImageProvider()
        self._video_provider = video_provider
        self._tts_provider = tts_provider or EdgeTTSProvider()
        self._model_manager = model_manager

    def run(
        self,
        script_path: str | None = None,
        *,
        job_id: str | None = None,
        output_path: str | None = None,
        title: str | None = None,
        width: int | None = None,
        height: int | None = None,
        fps: int | None = None,
        step: str = "all",
        force: bool = False,
        audio_mode: str = "tts",
        use_tts: bool = False,
        auto_confirm: bool = False,
        regenerate: int | None = None,
        user_images_dir: str | None = None,
    ) -> dict:
        if step not in SEEDANCE_STEPS:
            raise ValueError(f"Unknown Seedance step: {step}. Available: {SEEDANCE_STEPS}")

        start = time.perf_counter()
        width = width or self._cfg.video_width
        height = height or self._cfg.video_height
        fps = fps or self._cfg.video_fps
        job_id = job_id or make_job_id(title or "")

        job_dir = self._cfg.output_videos_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        plan_path = job_dir / "plan.json"
        image_dir = job_dir / "images"
        clip_dir = job_dir / "clips"
        final_path = Path(output_path) if output_path else job_dir / f"{job_id}.mp4"

        logger.info("=" * 50)
        logger.info(
            "ProduceSeedance START: script=%s job_id=%s step=%s size=%dx%d fps=%d "
            "audio_mode=%s auto_confirm=%s regenerate=%s",
            script_path, job_id, step, width, height, fps,
            audio_mode, auto_confirm, regenerate,
        )

        # ---- Step: plan ----
        if step in {"all", "plan"}:
            plan = self._prepare_plan(
                script_path=script_path,
                plan_path=plan_path,
                title=title,
                width=width,
                height=height,
                fps=fps,
                force=force,
            )
        else:
            if not plan_path.exists():
                raise FileNotFoundError(f"Plan not found: {plan_path}. Run --step plan first.")
            plan = video_plan_from_dict(read_json(plan_path))

        # ---- Step: unify (LLM 重写 image_prompt 保持角色一致) ----
        if step == "unify":
            plan = self._unify_prompts_with_llm(plan, force=force)
            write_json(plan_path, to_dict(plan))
            logger.info("[unify] Plan saved: %s", plan_path)
            return {
                "job_id": job_id,
                "plan_path": str(plan_path),
                "character_description": plan.character_description,
            }

        # ---- Step: images ----
        if step in {"all", "images"}:
            self._prepare_images(
                plan=plan,
                image_dir=image_dir,
                job_dir=job_dir,
                force=force,
                auto_confirm=auto_confirm,
                regenerate=regenerate,
                user_images_dir=user_images_dir,
            )

        # ---- Step: videos ----
        if step in {"all", "videos"}:
            if not self._video_provider:
                raise RuntimeError("Seedance video provider is not configured")
            self._prepare_clips(
                plan=plan,
                image_dir=image_dir,
                clip_dir=clip_dir,
                audio_mode=audio_mode,
                force=force,
            )

        # ---- Step: subtitles (SRT only) ----
        srt_path = job_dir / "subtitles.srt"
        if step in {"all", "subtitles"}:
            srt_path = self._prepare_subtitles(plan, job_dir, force=force)

        # ---- Step: compose ----
        audio_asset = None
        if step in {"all", "compose"}:
            # TTS 音频
            if audio_mode == "tts" and use_tts:
                audio_asset = self._prepare_audio(plan, job_dir, clip_dir, force=force)

            self._compose(
                plan=plan,
                clip_dir=clip_dir,
                final_path=final_path,
                audio_asset=audio_asset,
                fps=fps,
                force=force,
            )

        # ---- Burn subtitles into final video ----
        if step in {"all", "subtitles"}:
            if final_path.exists():
                subtitled_path = final_path.with_name(
                    final_path.stem + "_subtitled" + final_path.suffix
                )
                self._burn_subtitles(final_path, srt_path, subtitled_path, force=force)

        elapsed = time.perf_counter() - start
        logger.info(
            "ProduceSeedance DONE: job_id=%s video=%s scenes=%d elapsed=%.1fs",
            job_id, final_path, len(plan.scenes), elapsed,
        )
        return {
            "job_id": job_id,
            "video_path": str(final_path),
            "plan_path": str(plan_path),
            "image_dir": str(image_dir),
            "clip_dir": str(clip_dir),
            "audio_path": audio_asset.path if audio_asset else None,
        }

    # ---- plan ----

    def _prepare_plan(
        self,
        *,
        script_path: str | None,
        plan_path: Path,
        title: str | None,
        width: int,
        height: int,
        fps: int,
        force: bool,
    ) -> VideoPlan:
        if plan_path.exists() and not force:
            logger.info("[plan] Loading existing plan: %s", plan_path)
            plan = video_plan_from_dict(read_json(plan_path))
            logger.info("       -> %d scenes, %.1fs", len(plan.scenes), plan.total_duration)
            return plan

        if not script_path:
            raise ValueError("--script is required when creating a plan")

        logger.info("[plan] Splitting script into scenes ...")
        script = read_text(script_path)
        plan = self._splitter.split(script, title=title, width=width, height=height, fps=fps)
        write_json(plan_path, to_dict(plan))
        logger.info(
            "       -> %d scenes, %.1fs saved: %s",
            len(plan.scenes), plan.total_duration, plan_path,
        )
        for scene in plan.scenes:
            logger.info(
                "       scene %03d: %.1fs subtitle=%s",
                scene.index, scene.duration, scene.subtitle[:40],
            )
        return plan

    # ---- images ----

    def _unify_image_prompts(self, plan: VideoPlan) -> None:
        """确保所有场景的 image_prompt 包含统一的角色描述，保持画面一致性。"""
        char_desc = (plan.character_description or "").strip()
        if not char_desc:
            # 没有显式的 character_description，从第一个场景提取
            # 取 image_prompt 的前半部分（通常是角色描述）作为统一前缀
            first_prompt = plan.scenes[0].image_prompt if plan.scenes else ""
            # 尝试提取第一个逗号之前的内容作为角色描述
            parts = first_prompt.split("，", 1)
            if len(parts) > 1 and len(parts[0]) < 80:
                char_desc = parts[0]
            else:
                # 回退：取前 50 个字符
                char_desc = first_prompt[:50] if first_prompt else ""

        if not char_desc:
            return

        logger.info("[images] Unified character description: %s", char_desc[:60])
        for scene in plan.scenes:
            prompt = scene.image_prompt
            # 如果 prompt 已经以角色描述开头，跳过
            if prompt.startswith(char_desc):
                continue
            # 否则，去掉可能存在的旧角色描述前缀，统一加上新的
            # 简单策略：直接前置
            scene.image_prompt = f"{char_desc}，{prompt}"

    def _unify_prompts_with_llm(self, plan: VideoPlan, *, force: bool) -> VideoPlan:
        """用 LLM 生成统一角色描述并重写所有 image_prompt。"""
        if plan.character_description and not force:
            logger.info("[unify] Character description already exists, skipping. Use --force to regenerate.")
            return plan

        if not self._model_manager:
            raise RuntimeError("ModelManager is required for --step unify. Configure a model instance.")

        logger.info("[unify] Generating unified character description via LLM ...")

        scenes_summary = "\n".join(
            f"  场景{scene.index}: {scene.image_prompt[:120]}"
            for scene in plan.scenes
        )
        prompt = (
            f"以下是同一个短视频的{len(plan.scenes)}个分镜的图片生成提示词，但每个分镜描述的人物外观不一致。\n"
            f"请做两件事：\n"
            f"1. 从这些描述中总结出一个统一的角色外观描述（50字以内），包含性别、年龄范围、发型、穿着、体态等关键特征。\n"
            f"2. 为每个分镜重写 image_prompt：在开头加上统一角色描述，后面保留原场景的环境、构图、光线等描述，去掉原 prompt 中与角色冲突的部分。每个 prompt 末尾必须加上\"无文字无logo无水印\"，画面中绝对不能出现文字、字母、数字、字幕。\n"
            f"\n分镜提示词：\n{scenes_summary}\n"
            f"\n请严格输出 JSON，格式为：\n"
            f'{{"character_description": "统一角色描述", "scenes": [{{"index": 1, "image_prompt": "重写后的提示词"}}, ...]}}\n'
            f"不要输出任何其他内容。"
        )

        try:
            response = self._model_manager.generate(
                "scene_planner",  # 使用场景规划的模型实例
                prompt,
                system_prompt="你是一个短视频分镜脚本专家，擅长保持画面风格和角色一致性。",
            )
            import json
            import re
            text = response.strip()
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            start = min(
                (text.find(c) for c in "{["),
                key=lambda x: x if x >= 0 else 999999,
            )
            end = max(text.rfind("}"), text.rfind("]"))
            data = json.loads(text[start:end + 1])

            char_desc = str(data.get("character_description", "")).strip()
            scenes_data = data.get("scenes", [])

            if char_desc:
                plan.character_description = char_desc
                logger.info("[unify] Character description: %s", char_desc)

            # 更新各场景的 image_prompt
            scene_map = {s["index"]: s for s in scenes_data if "index" in s}
            for scene in plan.scenes:
                if scene.index in scene_map:
                    new_prompt = scene_map[scene.index].get("image_prompt", "")
                    if new_prompt:
                        scene.image_prompt = new_prompt
                        logger.info("       scene %03d: %s", scene.index, new_prompt[:80])

            logger.info("[unify] Done: %d scenes updated", len(scenes_data))

        except Exception:
            logger.warning("[unify] LLM unify failed, falling back to simple extraction", exc_info=True)
            self._unify_image_prompts(plan)

        return plan

    def _prepare_images(
        self,
        plan: VideoPlan,
        image_dir: Path,
        job_dir: Path,
        *,
        force: bool,
        auto_confirm: bool,
        regenerate: int | None,
        user_images_dir: str | None,
    ) -> None:
        image_dir.mkdir(parents=True, exist_ok=True)

        # 用户自定义图片模式
        if user_images_dir:
            self._load_user_images(plan, Path(user_images_dir), image_dir)
            return

        logger.info("[images] Generating scene reference images ...")

        # 统一角色描述，保证所有分镜的人物外观一致
        self._unify_image_prompts(plan)

        for i, scene in enumerate(plan.scenes):
            image_path = image_dir / scene_filename(scene.index, ".png")

            # 跳过已存在的图（除非 force 或 regenerate 指定）
            if image_path.exists() and not force:
                if regenerate and scene.index == regenerate:
                    pass  # 重新生成
                else:
                    logger.info("       [%d/%d] reuse: %s", i + 1, len(plan.scenes), image_path.name)
                    continue

            scene_start = time.perf_counter()
            if i == 0 or not self._find_previous_image(image_dir, i, plan.scenes):
                # 首镜或找不到前一张确认图：Seedream 文生图
                logger.info(
                    "       [%d/%d] text-to-image scene %03d ...",
                    i + 1, len(plan.scenes), scene.index,
                )
                self._image_provider.generate(
                    scene, image_dir, width=plan.width, height=plan.height,
                )
            else:
                # 后续镜：Seedream img2img 基于上一张确认图
                ref_path = self._find_previous_image(image_dir, i, plan.scenes)
                logger.info(
                    "       [%d/%d] img2img scene %03d (ref: %s) ...",
                    i + 1, len(plan.scenes), scene.index, ref_path.name,
                )
                self._image_provider.generate_from_ref(
                    ref_path, scene, image_dir, width=plan.width, height=plan.height,
                )

            logger.info(
                "       -> %s (%.1fs)",
                image_path.name, time.perf_counter() - scene_start,
            )

            # 交互确认
            if not auto_confirm:
                self._wait_user_confirm(scene.index, image_path)

        logger.info("[images] Done: %d images in %s", len(plan.scenes), image_dir)

    def _find_previous_image(self, image_dir: Path, current_i: int, scenes: list[Scene]) -> Path | None:
        """找到当前场景之前的最后一张已确认图片。"""
        for j in range(current_i - 1, -1, -1):
            prev_path = image_dir / scene_filename(scenes[j].index, ".png")
            if prev_path.exists():
                return prev_path
        return None

    def _load_user_images(self, plan: VideoPlan, user_dir: Path, image_dir: Path) -> None:
        """从用户指定目录加载参考图，按 scene_index 匹配。"""
        logger.info("[images] Loading user images from: %s", user_dir)
        copied = 0
        for scene in plan.scenes:
            # 尝试多种命名格式
            candidates = [
                user_dir / scene_filename(scene.index, ".png"),
                user_dir / scene_filename(scene.index, ".jpg"),
                user_dir / f"{scene.index}.png",
                user_dir / f"{scene.index}.jpg",
            ]
            src = None
            for c in candidates:
                if c.exists():
                    src = c
                    break
            if src is None:
                logger.warning("       scene %03d: no image found in %s", scene.index, user_dir)
                continue
            dest = image_dir / scene_filename(scene.index, ".png")
            if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime:
                import shutil
                shutil.copy2(src, dest)
                logger.info("       scene %03d: copied %s", scene.index, src.name)
            copied += 1
        logger.info("[images] Loaded %d user images", copied)

    def _wait_user_confirm(self, scene_index: int, image_path: Path) -> None:
        """等待用户确认图片。"""
        print(f"\n[确认] scene_{scene_index:03d} 参考图已生成: {image_path}")
        print("       查看后按 Enter 继续，输入 'r' 重新生成，输入 'q' 跳过后续确认: ", end="")
        try:
            choice = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if choice == "q":
            # 后续不再等待确认（修改 self 状态太脏，用文件标记）
            logger.info("User skipped remaining confirmations")
        elif choice == "r":
            logger.info("User requested regenerate scene %03d", scene_index)

    # ---- videos ----

    def _prepare_clips(
        self,
        plan: VideoPlan,
        image_dir: Path,
        clip_dir: Path,
        *,
        audio_mode: str,
        force: bool,
    ) -> None:
        clip_dir.mkdir(parents=True, exist_ok=True)
        generate_audio = audio_mode == "seedance-audio"

        # 如果 generate_audio 与 provider 配置不同，临时覆盖
        provider = self._video_provider
        if provider._generate_audio != generate_audio:
            provider = SeedanceVideoProvider(
                base_url=provider._base_url,
                api_key=provider._api_key,
                model=provider._model,
                resolution=provider._resolution,
                ratio=provider._ratio,
                duration=provider._duration,
                generate_audio=generate_audio,
                watermark=provider._watermark,
                timeout=provider._timeout,
                poll_interval=provider._poll_interval,
            )

        logger.info(
            "[videos] Generating Seedance video clips (audio=%s) ...",
            generate_audio,
        )
        for i, scene in enumerate(plan.scenes):
            clip_path = clip_dir / scene_filename(scene.index, ".mp4")
            if clip_path.exists() and not force:
                logger.info("       [%d/%d] reuse: %s", i + 1, len(plan.scenes), clip_path.name)
                continue

            image_path = image_dir / scene_filename(scene.index, ".png")
            if not image_path.exists():
                logger.warning("       [%d/%d] scene %03d: image missing, skipping",
                               i + 1, len(plan.scenes), scene.index)
                continue

            scene_start = time.perf_counter()
            logger.info(
                "       [%d/%d] scene %03d: generating video ...",
                i + 1, len(plan.scenes), scene.index,
            )
            try:
                provider.generate(
                    image_path,
                    scene.narration or scene.subtitle,
                    clip_path,
                    duration=max(2, int(scene.duration)),
                )
                logger.info(
                    "       -> %s (%.1fs)",
                    clip_path.name, time.perf_counter() - scene_start,
                )
            except Exception as exc:
                logger.error(
                    "       scene %03d video FAILED: %s (%.1fs)",
                    scene.index, exc, time.perf_counter() - scene_start,
                )

        logger.info("[videos] Done")

    # ---- subtitles ----

    def _prepare_subtitles(self, plan: VideoPlan, job_dir: Path, *, force: bool) -> Path:
        """生成 SRT 字幕文件。"""
        srt_path = job_dir / "subtitles.srt"
        if srt_path.exists() and not force:
            logger.info("[subtitles] Reusing SRT: %s", srt_path)
            return srt_path
        write_srt(plan, srt_path)
        logger.info("[subtitles] Generated SRT: %s", srt_path)
        return srt_path

    def _burn_subtitles(self, video_path: Path, srt_path: Path, output_path: Path, *, force: bool) -> str:
        """用 ffmpeg 将 SRT 字幕烧录到视频。"""
        if output_path.exists() and not force:
            logger.info("[subtitles] Reusing subtitled video: %s", output_path)
            return str(output_path)

        import subprocess

        # 先将 SRT 转换为 ASS 格式（ASS 路径处理更可靠，避免 Windows 路径冒号问题）
        ass_path = srt_path.with_suffix(".ass")
        convert_cmd = [
            "ffmpeg", "-y",
            "-i", str(srt_path),
            str(ass_path),
        ]
        result = subprocess.run(convert_cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"SRT to ASS conversion failed: {result.stderr[:300]}")

        # 修改 ASS 文件的样式
        self._style_ass(ass_path)

        # 用 ass 滤镜烧录字幕（比 subtitles 滤镜路径处理更可靠）
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"ass={ass_path.as_posix()}",
            "-c:a", "copy",
            str(output_path),
        ]
        logger.info("[subtitles] Burning subtitles: %s -> %s", video_path.name, output_path.name)
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg subtitle burn failed: {result.stderr[:500]}")
        logger.info("[subtitles] Done: %s", output_path)
        return str(output_path)

    def _style_ass(self, ass_path: Path) -> None:
        """修改 ASS 字幕文件的样式，优化显示效果。"""
        content = ass_path.read_text(encoding="utf-8")

        # 替换默认样式行
        old_style = "Style: Default,Arial,16,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1"
        new_style = "Style: Default,Microsoft YaHei,22,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,40,1"
        content = content.replace(old_style, new_style)

        ass_path.write_text(content, encoding="utf-8")

    # ---- audio ----

    def _prepare_audio(self, plan: VideoPlan, job_dir: Path, clip_dir: Path, *, force: bool) -> AudioAsset | None:
        audio_path = job_dir / "audio.mp3"
        if audio_path.exists() and not force:
            logger.info("[tts] Reusing audio: %s", audio_path)
            duration = self._audio_duration(audio_path)
            return AudioAsset(str(audio_path), duration=duration, provider="tts")

        logger.info("[tts] Generating per-scene TTS aligned to video clips ...")
        audio_dir = job_dir / "audio_clips"
        audio_dir.mkdir(parents=True, exist_ok=True)

        clip_paths = []

        for scene in plan.scenes:
            clip_path = audio_dir / f"scene_{scene.index:03d}.mp3"
            text = scene.narration or scene.subtitle
            if not text.strip():
                continue

            # 读取视频片段的实际时长
            video_clip_path = clip_dir / scene_filename(scene.index, ".mp4")
            if video_clip_path.exists():
                target_duration = self._audio_duration(video_clip_path)
            else:
                target_duration = scene.duration

            # 第一轮：用正常速率生成，实测 TTS 语速
            self._tts_provider.synthesize(
                text, clip_path,
                voice=self._cfg.tts_voice,
                rate=1.0,
            )
            actual_duration = self._audio_duration(clip_path)

            # 根据实测时长 vs 视频时长，计算需要的速率
            rate = 1.0
            if actual_duration > 0 and target_duration > 0:
                rate = actual_duration / target_duration
                rate *= 1.02  # 留 2% 余量，确保音频不超视频

            logger.info(
                "       scene %03d: tts=%.1fs video=%.1fs rate=%.2f",
                scene.index, actual_duration, target_duration, rate,
            )

            # 如果速率 > 1.02（需要加速），重新生成
            if rate > 1.02:
                rate = min(rate, 2.0)  # 上限 2x
                logger.info("       scene %03d: regenerating at rate=%.2f", scene.index, rate)
                self._tts_provider.synthesize(
                    text, clip_path,
                    voice=self._cfg.tts_voice,
                    rate=rate,
                )

            clip_paths.append(clip_path)

        if not clip_paths:
            logger.warning("[tts] No audio clips generated")
            return None

        # 用 ffmpeg 拼接所有音频片段
        concat_list = job_dir / "audio_concat.txt"
        concat_list.write_text(
            "\n".join(f"file '{p.as_posix()}'" for p in clip_paths),
            encoding="utf-8",
        )

        import subprocess
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(audio_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(f"Audio concat failed: {result.stderr[:300]}")

        duration = self._audio_duration(audio_path)
        logger.info("[tts] Done: %.1fs -> %s (%d clips)", duration, audio_path, len(clip_paths))
        return AudioAsset(str(audio_path), duration=duration, provider="tts")

    # ---- compose ----

    def _compose(
        self,
        plan: VideoPlan,
        clip_dir: Path,
        final_path: Path,
        audio_asset: AudioAsset | None,
        *,
        fps: int,
        force: bool,
    ) -> str:
        if final_path.exists() and not force:
            logger.info("[compose] Reusing video: %s", final_path)
            return str(final_path)

        try:
            from moviepy import AudioFileClip, concatenate_videoclips, VideoFileClip
        except ImportError:
            from moviepy.editor import AudioFileClip, concatenate_videoclips, VideoFileClip

        logger.info("[compose] Composing final video ...")
        final_path.parent.mkdir(parents=True, exist_ok=True)

        clips = []
        for scene in plan.scenes:
            clip_path = clip_dir / scene_filename(scene.index, ".mp4")
            if clip_path.exists():
                clip = VideoFileClip(str(clip_path))
                clips.append(clip)
                logger.info("       loading clip: %s (%.1fs)", clip_path.name, clip.duration)
            else:
                logger.warning("       clip missing for scene %03d, skipping", scene.index)

        if not clips:
            raise RuntimeError("No video clips to compose")

        final_clip = concatenate_videoclips(clips, method="compose")

        audio_clip = None
        if audio_asset:
            audio_clip = AudioFileClip(audio_asset.path)
            # 如果音频比视频长，延长视频到最后一个画面
            if audio_clip.duration and audio_clip.duration > final_clip.duration:
                logger.info(
                    "[compose] Audio (%.1fs) longer than video (%.1fs), extending video",
                    audio_clip.duration, final_clip.duration,
                )
                final_clip = final_clip.with_duration(audio_clip.duration)
            final_clip = final_clip.with_audio(audio_clip)

        final_clip.write_videofile(
            str(final_path),
            fps=fps,
            codec="libx264",
            audio_codec="aac" if audio_asset else None,
            ffmpeg_params=["-pix_fmt", "yuv420p"],
            logger="bar",
        )

        # 关闭 clips
        for clip in clips:
            clip.close()
        final_clip.close()
        if audio_clip:
            audio_clip.close()

        logger.info("[compose] Done: %s", final_path)
        return str(final_path)

    def _audio_duration(self, media_path: Path) -> float:
        """用 ffprobe 获取媒体文件时长，避免 moviepy FFMPEG_AudioReader 兼容性问题。"""
        import subprocess
        import json
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-print_format", "json",
                 "-show_format", str(media_path)],
                capture_output=True, text=True, encoding="utf-8",
            )
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0.0))
        except Exception:
            return 0.0

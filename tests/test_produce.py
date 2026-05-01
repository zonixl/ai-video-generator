"""文案到视频生产链路测试。"""

from pathlib import Path

from core.schema import AudioAsset, ClipAsset, ImageAsset


def test_rule_based_scene_splitter_creates_plan():
    from core.scene_splitter import RuleBasedSceneSplitter

    splitter = RuleBasedSceneSplitter(min_scene_duration=2, max_scene_duration=4)
    plan = splitter.split(
        "# 人工智能趋势\n人工智能正在改变内容生产。它可以帮助创作者提高效率！但最终质量仍然取决于人的判断。",
        style="clean",
        width=720,
        height=1280,
        fps=24,
    )

    assert plan.title == "人工智能趋势"
    assert plan.width == 720
    assert plan.height == 1280
    assert plan.fps == 24
    assert len(plan.scenes) >= 1
    assert plan.scenes[0].subtitle
    assert plan.scenes[0].duration >= 2


def test_subtitle_srt_timeline():
    from core.schema import Scene, VideoPlan
    from utils.subtitle_utils import build_srt

    plan = VideoPlan(
        title="测试",
        script="第一句。第二句。",
        scenes=[
            Scene(1, "第一句。", "第一句。", "画面一", "prompt", 2.5),
            Scene(2, "第二句。", "第二句。", "画面二", "prompt", 3.0),
        ],
    )

    srt = build_srt(plan, max_chars=10)

    assert "00:00:00,000 --> 00:00:02,500" in srt
    assert "00:00:02,500 --> 00:00:05,500" in srt
    assert "第一句。" in srt


def test_produce_pipeline_no_tts_writes_expected_outputs(tmp_path):
    from pipeline.produce import ProducePipeline

    script_path = tmp_path / "script.md"
    script_path.write_text("# 测试视频\n这是第一段文案。这里说明第二个观点。", encoding="utf-8")

    config = FakeProduceConfig(tmp_path)
    pipeline = ProducePipeline(
        config,
        image_provider=FakeImageProvider(),
        renderer=FakeRenderer(),
    )

    result = pipeline.run(str(script_path), use_tts=False)

    assert Path(result.plan_path).exists()
    assert Path(result.subtitle_path).exists()
    assert Path(result.video_path).exists()
    assert result.audio_path is None
    assert result.image_paths
    assert result.clip_paths


def test_produce_pipeline_logs_progress(tmp_path, caplog):
    from pipeline.produce import ProducePipeline

    script_path = tmp_path / "script.md"
    script_path.write_text("# 测试视频\n这是第一段文案。这里说明第二个观点。", encoding="utf-8")

    config = FakeProduceConfig(tmp_path)
    pipeline = ProducePipeline(
        config,
        image_provider=FakeImageProvider(),
        renderer=FakeRenderer(),
    )

    with caplog.at_level("INFO"):
        pipeline.run(str(script_path), use_tts=False)

    log_text = caplog.text
    assert "[1/7] Splitting script into scenes" in log_text
    assert "[4/7] Generating images" in log_text
    assert "[5/7] Rendering animated scene clips" in log_text
    assert "ProducePipeline DONE" in log_text


def test_produce_pipeline_reuses_existing_job_assets(tmp_path):
    from pipeline.produce import ProducePipeline

    script_path = tmp_path / "script.md"
    script_path.write_text("# 测试视频\n这是第一段文案。这里说明第二个观点。", encoding="utf-8")

    config = FakeProduceConfig(tmp_path)
    provider = CountingImageProvider()
    pipeline = ProducePipeline(config, image_provider=provider, renderer=FakeRenderer())

    first = pipeline.run(str(script_path), job_id="video_fixed", use_tts=False)
    assert provider.calls > 0

    provider.calls = 0
    second = pipeline.run(
        job_id="video_fixed",
        step="images",
        reuse_assets=True,
    )

    assert second.job_id == first.job_id
    assert provider.calls == 0
    assert second.image_paths == first.image_paths


def test_produce_pipeline_can_add_tts_to_existing_job(tmp_path):
    from pipeline.produce import ProducePipeline
    from utils.file_utils import read_json

    script_path = tmp_path / "script.md"
    script_path.write_text("# 测试视频\n这是第一段文案。这里说明第二个观点。", encoding="utf-8")

    config = FakeProduceConfig(tmp_path)
    pipeline = ProducePipeline(
        config,
        image_provider=FakeImageProvider(),
        renderer=FakeRenderer(),
        tts_provider=FakeTTSProvider(duration=4.0),
    )

    pipeline.run(str(script_path), job_id="video_audio", use_tts=False)
    result = pipeline.run(job_id="video_audio", step="tts", use_tts=True, force=True)

    assert result.audio_path is not None
    assert Path(result.audio_path).exists()
    assert Path(result.audio_path).parent == config.output_videos_dir
    plan_data = read_json(result.plan_path)
    total_duration = sum(scene["duration"] for scene in plan_data["scenes"])
    assert round(total_duration, 1) == 4.0


class FakeProduceConfig:
    def __init__(self, root: Path):
        self.output_audio_dir = root / "audio"
        self.output_images_dir = root / "images"
        self.output_videos_dir = root / "videos"
        self.output_clips_dir = root / "clips"
        self.output_subtitles_dir = root / "subtitles"
        self.output_plans_dir = root / "plans"
        self.video_width = 720
        self.video_height = 1280
        self.video_fps = 12
        self.video_min_scene_duration = 1.0
        self.video_max_scene_duration = 2.0
        self.video_chars_per_second = 8.0
        self.video_subtitle_max_chars = 12
        self.tts_voice = "zh-CN-XiaoxiaoNeural"
        self.tts_speed = 1.0


class FakeImageProvider:
    def generate(self, scene, output_dir, *, width: int, height: int) -> ImageAsset:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"scene_{scene.index:03d}.png"
        path.write_bytes(b"fake image")
        return ImageAsset(scene.index, str(path), provider="fake", prompt=scene.image_prompt)


class CountingImageProvider(FakeImageProvider):
    def __init__(self):
        self.calls = 0

    def generate(self, scene, output_dir, *, width: int, height: int) -> ImageAsset:
        self.calls += 1
        return super().generate(scene, output_dir, width=width, height=height)


class FakeTTSProvider:
    def __init__(self, duration: float):
        self.duration = duration

    def synthesize(self, text: str, output_path, *, voice: str, rate: float = 1.0) -> AudioAsset:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake audio")
        return AudioAsset(str(output_path), self.duration, provider="fake", voice=voice)


class FakeRenderer:
    def render_scene(self, scene, image, output_dir, *, width: int, height: int, fps: int) -> ClipAsset:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"scene_{scene.index:03d}.mp4"
        path.write_bytes(b"fake clip")
        return ClipAsset(scene.index, str(path), scene.duration)

    def compose(self, plan, clips, output_path, *, audio=None) -> str:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake video")
        return str(output_path)


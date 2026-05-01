"""Remotion 独立视频流程测试。"""

from pathlib import Path

from core.remotion_schema import RemotionComponentSpec, RemotionSceneSpec, RemotionVideoSpec


def test_rule_based_remotion_planner_creates_spec():
    from core.remotion_planner import RuleBasedRemotionPlanner

    spec = RuleBasedRemotionPlanner().plan(
        "# 测试\nAI 先规划图示。然后 Remotion 渲染组件。",
        title=None,
        width=720,
        height=1280,
        fps=24,
    )

    assert spec.title == "测试"
    assert spec.width == 720
    assert spec.height == 1280
    assert spec.fps == 24
    assert spec.scenes
    assert spec.scenes[0].components


def test_ai_remotion_planner_parses_scene_json():
    from core.remotion_planner import AIRemotionPlanner

    spec = AIRemotionPlanner(FakeModelManager()).plan(
        "# 测试\n从旧方式切换到新方式。",
        title=None,
        width=1080,
        height=1920,
        fps=30,
    )

    assert spec.scenes[0].headline == "实验"
    assert spec.scenes[0].components[0].slot == "left_top"
    assert spec.scenes[0].components[0].motion == "strike"
    assert spec.scenes[0].components[0].icon == "x"
    assert spec.scenes[0].components[2].type == "comparison"


def test_produce_remotion_plan_writes_input(tmp_path):
    from pipeline.produce_remotion import ProduceRemotionPipeline
    from utils.file_utils import read_json

    script_path = tmp_path / "script.md"
    script_path.write_text("# 测试\nAI 生成 JSON。Remotion 渲染。", encoding="utf-8")
    pipeline = ProduceRemotionPipeline(
        FakeConfig(tmp_path),
        planner=FakePlanner(),
        renderer=FakeRenderer(),
    )

    result = pipeline.run(str(script_path), job_id="remotion_test", step="plan", force=True)

    assert result.rendered is False
    assert Path(result.input_path).exists()
    data = read_json(result.input_path)
    assert data["title"] == "测试 Remotion"
    assert data["scenes"][0]["template"] == "basic_diagram"


def test_produce_remotion_render_uses_existing_input(tmp_path):
    from pipeline.produce_remotion import ProduceRemotionPipeline
    from utils.file_utils import write_json

    config = FakeConfig(tmp_path)
    input_path = config.output_remotion_dir / "remotion_test" / "input.json"
    write_json(input_path, _fake_spec_dict())
    renderer = FakeRenderer()
    pipeline = ProduceRemotionPipeline(config, planner=FakePlanner(), renderer=renderer)

    result = pipeline.run(job_id="remotion_test", step="render")

    assert result.rendered is True
    assert renderer.calls == 1
    assert Path(result.video_path).exists()


class FakeConfig:
    def __init__(self, root: Path):
        self.output_remotion_dir = root / "remotion"
        self.output_videos_dir = root / "videos"
        self.video_width = 720
        self.video_height = 1280
        self.video_fps = 24
        self.remotion_project_dir = root / "remotion_project"
        self.remotion_refine_enabled = False
        self.remotion_refine_rounds = 2


class FakePlanner:
    def plan(self, script: str, *, title: str | None, width: int, height: int, fps: int) -> RemotionVideoSpec:
        return RemotionVideoSpec(
            title="测试 Remotion",
            width=width,
            height=height,
            fps=fps,
            scenes=[
                RemotionSceneSpec(
                    scene_index=1,
                    duration=5,
                    headline="实验",
                    subtitle="AI 生成 JSON。",
                    components=[
                        RemotionComponentSpec("a", "card", "left_top", "旧流程", "danger", "strike", "x"),
                        RemotionComponentSpec("arrow", "arrow", "center", "", "default", "draw"),
                        RemotionComponentSpec("b", "card", "right_top", "新流程", "success", "pop", "check"),
                    ],
                )
            ],
        )


class FakeRenderer:
    def __init__(self):
        self.calls = 0

    def render(self, input_path, output_path) -> str:
        self.calls += 1
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake video")
        return str(output_path)


class FakeModelManager:
    def generate(self, instance_name: str, prompt: str, system_prompt: str | None = None) -> str:
        assert instance_name == "remotion_designer"
        assert "basic_diagram" in prompt
        return """
        {
          "scene_index": 1,
          "duration": 5,
          "template": "basic_diagram",
          "theme": "warm_grid",
          "headline": "实验",
          "subtitle": "从旧方式切换到新方式。",
          "components": [
            {"id": "old", "type": "card", "slot": "left_top", "text": "旧方式", "variant": "danger", "motion": "strike", "icon": "x"},
            {"id": "arrow", "type": "arrow", "slot": "center", "text": "", "variant": "default", "motion": "draw"},
            {"id": "new", "type": "comparison", "slot": "right_top", "text": "旧方式|34|新方式|89", "variant": "success", "motion": "pop", "icon": "check"}
          ]
        }
        """


def _fake_spec_dict():
    return {
        "title": "测试 Remotion",
        "width": 720,
        "height": 1280,
        "fps": 24,
        "scenes": [
            {
                "scene_index": 1,
                "duration": 5,
                "template": "basic_diagram",
                "theme": "warm_grid",
                "headline": "实验",
                "subtitle": "测试字幕",
                "components": [
                    {"id": "a", "type": "bar_chart", "slot": "left_top", "text": "规划:80;渲染:90", "variant": "primary", "motion": "pop", "icon": "target"}
                ],
            }
        ],
    }


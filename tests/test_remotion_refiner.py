"""Remotion 视觉自迭代测试。"""

from pathlib import Path

from utils.file_utils import read_json, write_json


def test_parse_review_result_filters_invalid_patch_values():
    from core.remotion_review import parse_review_result

    result = parse_review_result("""
    {
      "pass": false,
      "score": 61,
      "issues": [{"type": "overlap", "severity": "high", "scene_index": 1, "reason": "too close"}],
      "patches": [{
        "scene_index": 1,
        "layout": "bad_layout",
        "theme": "clean",
        "replace_component_type": {"a": "unknown", "b": "card"},
        "set_motion": {"a": "fly", "b": "fade_in"},
        "limit_components": 99
      }]
    }
    """)

    assert result.passed is False
    assert result.score == 61
    assert result.patches[0].layout is None
    assert result.patches[0].theme == "clean"
    assert result.patches[0].replace_component_type == {"b": "card"}
    assert result.patches[0].set_motion == {"b": "fade_in"}
    assert result.patches[0].limit_components == 4


def test_refiner_applies_safe_patches(tmp_path):
    from core.remotion_refiner import RemotionRefiner

    input_path = tmp_path / "input.json"
    write_json(input_path, _spec())
    renderer = FakeRenderer()
    refiner = RemotionRefiner(
        renderer=renderer,
        vision_provider=FakeVisionProvider(pass_after=2),
        output_remotion_dir=tmp_path,
        frames_per_scene=1,
    )

    result = refiner.refine(input_path=input_path, job_id="demo", max_rounds=2)
    data = read_json(input_path)

    assert result.passed is True
    assert renderer.stills == 2
    assert data["scenes"][0]["layout"] == "center_focus"
    assert data["scenes"][0]["components"][0]["id"] == "a"
    assert data["scenes"][0]["components"][0]["text"] == "短文案"
    assert len(data["scenes"][0]["components"]) == 1
    assert (tmp_path / "demo" / "reviews" / "round_01" / "review.round_01.json").exists()


def test_refiner_review_only_does_not_apply_patch(tmp_path):
    from core.remotion_refiner import RemotionRefiner

    input_path = tmp_path / "input.json"
    write_json(input_path, _spec())
    refiner = RemotionRefiner(
        renderer=FakeRenderer(),
        vision_provider=FakeVisionProvider(pass_after=99),
        output_remotion_dir=tmp_path,
        frames_per_scene=1,
    )

    result = refiner.refine(input_path=input_path, job_id="demo", max_rounds=2, review_only=True)
    data = read_json(input_path)

    assert result.passed is False
    assert data["scenes"][0].get("layout") != "center_focus"
    assert len(data["scenes"][0]["components"]) == 2


class FakeRenderer:
    def __init__(self):
        self.stills = 0

    def render_still(self, input_path, output_path, frame):
        self.stills += 1
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake image")
        return str(output_path)


class FakeVisionProvider:
    def __init__(self, pass_after: int):
        self.calls = 0
        self.pass_after = pass_after

    def review(self, prompt: str, image_paths):
        self.calls += 1
        if self.calls >= self.pass_after:
            return '{"pass": true, "score": 95, "issues": [], "patches": []}'
        return """
        {
          "pass": false,
          "score": 68,
          "issues": [{"type": "crowded", "severity": "high", "scene_index": 1, "reason": "too many components"}],
          "patches": [{
            "scene_index": 1,
            "layout": "center_focus",
            "remove_component_ids": ["b"],
            "shorten_text": {"a": "短文案"},
            "limit_components": 1
          }]
        }
        """


def _spec():
    return {
        "title": "demo",
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "scenes": [
            {
                "scene_index": 1,
                "duration": 5,
                "template": "basic_diagram",
                "theme": "warm_grid",
                "headline": "测试",
                "subtitle": "字幕",
                "components": [
                    {"id": "a", "type": "card", "slot": "left_top", "text": "很长很长的文案", "variant": "primary", "motion": "pop"},
                    {"id": "b", "type": "notification", "slot": "bottom", "text": "通知", "variant": "success", "motion": "pop"},
                ],
            }
        ],
    }

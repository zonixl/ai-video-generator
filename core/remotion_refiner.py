"""Remotion 视觉审查与 DSL 自迭代修正。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from core import prompts
from core.remotion_renderer import RemotionRenderer
from core.remotion_review import ReviewPatch, ReviewResult, parse_review_result
from core.vision_provider import VisionProvider
from utils.file_utils import read_json, write_json

logger = logging.getLogger(__name__)


class RemotionRefiner:
    """render still -> vision review -> safe patch -> repeat."""

    def __init__(
        self,
        *,
        renderer: RemotionRenderer,
        vision_provider: VisionProvider,
        output_videos_dir: str | Path,
        frames_per_scene: int = 3,
    ):
        self._renderer = renderer
        self._vision = vision_provider
        self._output_videos_dir = Path(output_videos_dir)
        self._frames_per_scene = max(1, min(3, int(frames_per_scene)))

    def refine(
        self,
        *,
        input_path: str | Path,
        job_id: str,
        max_rounds: int = 2,
        review_only: bool = False,
    ) -> ReviewResult:
        input_path = Path(input_path)
        latest_result: ReviewResult | None = None
        for round_index in range(1, max(1, max_rounds) + 1):
            spec = read_json(input_path)
            round_dir = self._output_videos_dir / job_id / "reviews" / f"round_{round_index:02d}"
            frames = self._render_review_frames(input_path, spec, round_dir)
            result = self._review(spec, frames)
            latest_result = result

            write_json(round_dir / f"review.round_{round_index:02d}.json", result.to_dict())
            write_json(round_dir / f"input.round_{round_index:02d}.json", spec)
            logger.info(
                "Remotion review round %d: pass=%s score=%d issues=%d patches=%d",
                round_index, result.passed, result.score, len(result.issues), len(result.patches),
            )

            if result.passed or review_only or not result.patches:
                break

            patched = self._apply_patches(spec, result.patches)
            write_json(input_path, patched)

        if latest_result is None:
            raise RuntimeError("Remotion refine did not run any review round")
        return latest_result

    def _render_review_frames(self, input_path: Path, spec: dict, round_dir: Path) -> list[Path]:
        fps = int(spec.get("fps", 30))
        frames: list[Path] = []
        start_frame = 0
        for scene in spec.get("scenes", []):
            scene_index = int(scene.get("scene_index", len(frames) + 1))
            duration_frames = max(1, int(float(scene.get("duration", 5.0)) * fps))
            offsets = self._frame_offsets(duration_frames, fps)
            for offset in offsets:
                frame = start_frame + offset
                output = round_dir / f"scene_{scene_index:03d}_frame_{frame:05d}.png"
                self._renderer.render_still(input_path, output, frame)
                frames.append(output)
            start_frame += duration_frames
        return frames

    def _frame_offsets(self, duration_frames: int, fps: int) -> list[int]:
        candidates = [
            min(duration_frames - 1, int(0.8 * fps)),
            duration_frames // 2,
            max(0, duration_frames - int(0.6 * fps)),
        ]
        unique = []
        for frame in candidates[:self._frames_per_scene]:
            if frame not in unique:
                unique.append(frame)
        return unique or [0]

    def _review(self, spec: dict, frames: list[Path]) -> ReviewResult:
        prompt = prompts.REVIEW_REMOTION_FRAMES.format(
            spec_json=json.dumps(_compact_spec(spec), ensure_ascii=False, indent=2)
        )
        response = self._vision.review(prompt, frames)
        return parse_review_result(response)

    def _apply_patches(self, spec: dict, patches: list[ReviewPatch]) -> dict:
        scenes = spec.get("scenes", [])
        for patch in patches:
            scene = next((item for item in scenes if int(item.get("scene_index", 0)) == patch.scene_index), None)
            if not scene:
                continue
            if patch.layout:
                scene["layout"] = patch.layout
            if patch.theme:
                scene["theme"] = patch.theme
            components = scene.get("components", [])
            if patch.remove_component_ids:
                components = [item for item in components if item.get("id") not in patch.remove_component_ids]
            for component in components:
                component_id = str(component.get("id", ""))
                if component_id in patch.replace_component_type:
                    component["type"] = patch.replace_component_type[component_id]
                if component_id in patch.shorten_text:
                    component["text"] = patch.shorten_text[component_id]
                if component_id in patch.set_motion:
                    component["motion"] = patch.set_motion[component_id]
                if component_id in patch.set_variant:
                    component["variant"] = patch.set_variant[component_id]
            if patch.limit_components:
                backgrounds = [item for item in components if item.get("type") == "background_pattern"]
                non_backgrounds = [item for item in components if item.get("type") != "background_pattern"]
                components = backgrounds[:1] + non_backgrounds[:patch.limit_components]
            scene["components"] = components
        return spec


def _compact_spec(spec: dict) -> dict:
    return {
        "title": spec.get("title"),
        "fps": spec.get("fps"),
        "scenes": [
            {
                "scene_index": scene.get("scene_index"),
                "layout": scene.get("layout"),
                "headline": scene.get("headline"),
                "subtitle": scene.get("subtitle"),
                "components": [
                    {
                        "id": component.get("id"),
                        "type": component.get("type"),
                        "slot": component.get("slot"),
                        "text": component.get("text"),
                    }
                    for component in scene.get("components", [])
                ],
            }
            for scene in spec.get("scenes", [])
        ],
    }

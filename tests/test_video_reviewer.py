"""已生成视频视觉审查测试。"""

from pathlib import Path

from utils.file_utils import read_json


def test_sample_times_cover_video_range():
    from core.video_reviewer import sample_times

    times = sample_times(100.0, 5)

    assert len(times) == 5
    assert times[0] == 8.0
    assert times[-1] == 92.0
    assert times == sorted(times)


def test_video_reviewer_writes_review_and_metadata(tmp_path):
    from core.video_reviewer import VideoReviewer

    video = tmp_path / "demo.mp4"
    video.write_bytes(b"fake video")
    provider = FakeVisionProvider()
    reviewer = VideoReviewer(
        vision_provider=provider,
        output_dir=tmp_path / "reviews",
        extractor=FakeExtractor(),
    )

    result = reviewer.review(video, job_id="demo_review", frame_count=3)

    assert Path(result.review_path).read_text(encoding="utf-8") == "画面审查通过"
    assert len(result.frame_paths) == 3
    assert "demo.mp4" in provider.prompt
    assert len(provider.image_paths) == 3
    metadata = read_json(tmp_path / "reviews" / "demo_review" / "review_meta.json")
    assert metadata["duration"] == 12.5
    assert metadata["review_path"] == result.review_path


class FakeVisionProvider:
    def __init__(self):
        self.prompt = ""
        self.image_paths = []

    def review(self, prompt: str, image_paths):
        self.prompt = prompt
        self.image_paths = image_paths
        return "画面审查通过"


class FakeExtractor:
    def extract_frames(self, video_path, output_dir, frame_count):
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        frames = []
        for index in range(frame_count):
            frame = output_dir / f"frame_{index + 1:02d}.jpg"
            frame.write_bytes(b"fake image")
            frames.append(frame)
        return 12.5, frames

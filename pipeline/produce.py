"""多媒体生产管道：文案→语音/图片/视频（预留扩展点）。"""


class ProducePipeline:
    """Phase 3-4: 多媒体输出管道。当前为空壳，预留接口。"""

    def text_to_speech(self, script: str, output_path: str | None = None,
                       voice: str = "default") -> str:
        """Phase 3: 文案→语音文件。"""
        raise NotImplementedError("Phase 3: TTS - 待实现 (edge-tts / Coqui TTS)")

    def script_to_images(self, script: str, style: str = "realistic") -> list[str]:
        """Phase 3: 文案→分镜图片列表。"""
        raise NotImplementedError("Phase 3: Image generation - 待实现")

    def compose_video(
        self,
        images: list[str],
        audio: str,
        script: str,
        output_path: str,
        fps: int = 30,
        transition: str = "fade",
    ) -> str:
        """Phase 4: 图片+语音+字幕→合成视频。"""
        raise NotImplementedError("Phase 4: Video composition - 待实现 (moviepy/ffmpeg)")

    def add_subtitles(self, video_path: str, script: str) -> str:
        """Phase 4: 视频嵌字幕。"""
        raise NotImplementedError("Phase 4: Subtitles - 待实现")

"""图片生成 Provider。"""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from pathlib import Path
import textwrap

from core.schema import ImageAsset, Scene
from utils.media_utils import scene_filename

logger = logging.getLogger(__name__)


class ImageProvider(ABC):
    """图片生成抽象接口。"""

    @abstractmethod
    def generate(self, scene: Scene, output_dir: str | Path, *, width: int, height: int) -> ImageAsset:
        ...


class PlaceholderImageProvider(ImageProvider):
    """用 Pillow 生成竖屏占位图，供整条视频链路低成本跑通。"""

    provider_name = "placeholder"

    def generate(self, scene: Scene, output_dir: str | Path, *, width: int, height: int) -> ImageAsset:
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError as exc:
            raise RuntimeError("PlaceholderImageProvider 需要安装 pillow") from exc

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / scene_filename(scene.index, ".png")
        logger.debug(
            "Placeholder image start: scene=%03d size=%dx%d path=%s",
            scene.index, width, height, image_path,
        )

        image = Image.new("RGB", (width, height), self._background_color(scene.index))
        draw = ImageDraw.Draw(image)
        title_font = self._font(ImageFont, 72)
        body_font = self._font(ImageFont, 44)
        small_font = self._font(ImageFont, 32)

        self._draw_gradient(draw, width, height, scene.index)
        self._draw_centered_text(
            draw,
            f"Scene {scene.index:02d}",
            y=int(height * 0.16),
            width=width,
            font=small_font,
            fill=(230, 235, 255),
        )
        self._draw_wrapped_text(
            draw,
            scene.visual,
            x=int(width * 0.09),
            y=int(height * 0.32),
            width=int(width * 0.82),
            font=title_font,
            fill=(255, 255, 255),
            line_spacing=18,
            max_chars=12,
        )
        self._draw_wrapped_text(
            draw,
            scene.subtitle,
            x=int(width * 0.1),
            y=int(height * 0.72),
            width=int(width * 0.8),
            font=body_font,
            fill=(245, 245, 245),
            line_spacing=12,
            max_chars=16,
        )
        image.save(image_path)
        logger.debug("Placeholder image done: scene=%03d path=%s", scene.index, image_path)
        return ImageAsset(
            scene_index=scene.index,
            path=str(image_path),
            provider=self.provider_name,
            prompt=scene.image_prompt,
        )

    def _font(self, image_font, size: int):
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        for path in candidates:
            if Path(path).exists():
                return image_font.truetype(path, size=size)
        return image_font.load_default()

    def _background_color(self, index: int) -> tuple[int, int, int]:
        palette = [
            (31, 44, 84),
            (54, 39, 91),
            (34, 77, 92),
            (87, 48, 48),
            (42, 74, 55),
        ]
        return palette[(index - 1) % len(palette)]

    def _draw_gradient(self, draw, width: int, height: int, index: int) -> None:
        base = self._background_color(index)
        for y in range(height):
            ratio = y / max(height - 1, 1)
            color = tuple(min(255, int(channel + 42 * ratio)) for channel in base)
            draw.line([(0, y), (width, y)], fill=color)

    def _draw_centered_text(self, draw, text: str, *, y: int, width: int, font, fill) -> None:
        bbox = draw.textbbox((0, 0), text, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), text, font=font, fill=fill)

    def _draw_wrapped_text(
        self,
        draw,
        text: str,
        *,
        x: int,
        y: int,
        width: int,
        font,
        fill,
        line_spacing: int,
        max_chars: int,
    ) -> None:
        lines = textwrap.wrap(text, width=max_chars, break_long_words=True)
        current_y = y
        for line in lines[:6]:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_x = x + max(0, (width - (bbox[2] - bbox[0])) // 2)
            draw.text((line_x, current_y), line, font=font, fill=fill)
            current_y += (bbox[3] - bbox[1]) + line_spacing


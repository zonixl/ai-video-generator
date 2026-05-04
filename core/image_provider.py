"""图片生成 Provider。"""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
import logging
from pathlib import Path
import textwrap
from urllib.request import urlopen

from core.schema import ImageAsset, Scene
from utils.media_utils import scene_filename

logger = logging.getLogger(__name__)


class ImageProvider(ABC):
    """图片生成抽象接口。"""

    @abstractmethod
    def generate(self, scene: Scene, output_dir: str | Path, *, width: int, height: int, template: str = "") -> ImageAsset:
        ...

    def generate_from_ref(
        self,
        ref_image_path: str | Path,
        scene: Scene,
        output_dir: str | Path,
        *,
        width: int,
        height: int,
    ) -> ImageAsset:
        """基于参考图生成新图（img2img）。默认回退到纯文生图。"""
        logger.info("generate_from_ref not overridden, falling back to text-to-image")
        return self.generate(scene, output_dir, width=width, height=height)


class PlaceholderImageProvider(ImageProvider):
    """用 Pillow 生成竖屏占位图，供整条视频链路低成本跑通。"""

    provider_name = "placeholder"

    def generate(self, scene: Scene, output_dir: str | Path, *, width: int, height: int, template: str = "") -> ImageAsset:
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


class ArkSeedreamImageProvider(ImageProvider):
    """火山 Ark 豆包 Seedream 图片生成 Provider。"""

    provider_name = "ark-seedream"

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        size: str = "2K",
        watermark: bool = True,
        timeout: int = 180,
        client=None,
        downloader=None,
    ):
        self._base_url = base_url
        self._api_key = api_key
        self._model = model
        self._size = size
        self._watermark = watermark
        self._timeout = timeout
        self._client = client
        self._downloader = downloader or self._download_url

    def generate(self, scene: Scene, output_dir: str | Path, *, width: int, height: int, template: str = "") -> ImageAsset:
        if not self._api_key:
            raise RuntimeError("ArkSeedreamImageProvider 需要配置 image_gen.api_key 或 ARK_API_KEY")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / scene_filename(scene.index, ".png")
        prompt = self._build_prompt(scene, width, height, template)
        size = self._size_for_template(width, height, template)
        logger.info(
            "Ark Seedream image start: scene=%03d model=%s size=%s template=%s prompt_len=%d",
            scene.index, self._model, size, template, len(prompt),
        )
        response = self._client_or_create().images.generate(
            model=self._model,
            prompt=prompt,
            size=size,
            response_format="url",
            extra_body={"watermark": self._watermark},
        )
        image_url = response.data[0].url
        if not image_url:
            raise RuntimeError("Ark Seedream did not return image url")
        self._downloader(image_url, image_path)
        logger.info("Ark Seedream image done: scene=%03d path=%s", scene.index, image_path)
        return ImageAsset(
            scene_index=scene.index,
            path=str(image_path),
            provider=self.provider_name,
            prompt=prompt,
        )

    def generate_from_ref(
        self,
        ref_image_path: str | Path,
        scene: Scene,
        output_dir: str | Path,
        *,
        width: int,
        height: int,
    ) -> ImageAsset:
        """基于参考图生成新图（img2img），保持风格一致。"""
        if not self._api_key:
            raise RuntimeError("ArkSeedreamImageProvider 需要配置 image_gen.api_key")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / scene_filename(scene.index, ".png")
        prompt = self._build_prompt(scene, width, height)
        size = self._size_for_template(width, height, "")

        # 编码参考图为 base64
        ref_path = Path(ref_image_path)
        ref_b64 = base64.b64encode(ref_path.read_bytes()).decode()
        ref_mime = "image/png" if ref_path.suffix.lower() == ".png" else "image/jpeg"

        logger.info(
            "Ark Seedream img2img start: scene=%03d ref=%s size=%s prompt_len=%d",
            scene.index, ref_path.name, size, len(prompt),
        )
        response = self._client_or_create().images.generate(
            model=self._model,
            prompt=prompt,
            size=size,
            response_format="url",
            extra_body={
                "watermark": self._watermark,
                "image": f"data:{ref_mime};base64,{ref_b64}",
            },
        )
        image_url = response.data[0].url
        if not image_url:
            raise RuntimeError("Ark Seedream img2img did not return image url")
        self._downloader(image_url, image_path)
        logger.info("Ark Seedream img2img done: scene=%03d path=%s", scene.index, image_path)
        return ImageAsset(
            scene_index=scene.index,
            path=str(image_path),
            provider=self.provider_name,
            prompt=prompt,
        )

    def _client_or_create(self):
        if self._client is not None:
            return self._client
        from openai import OpenAI

        self._client = OpenAI(
            base_url=self._base_url,
            api_key=self._api_key,
            timeout=self._timeout,
        )
        return self._client

    def _build_prompt(self, scene: Scene, width: int, height: int, template: str = "") -> str:
        from core.template_registry import get_image_size
        img_size = get_image_size(template)

        # 方式 2 已指定精确尺寸，prompt 中补充构图要求
        if img_size == "full":
            style_hint = (
                "画面上方1/3和底部1/4区域必须偏暗或有深色渐变遮罩，"
                "确保白色文字叠上去清晰可读。中间区域为主体。"
            )
        elif img_size == "card_portrait":
            style_hint = "竖构图，主体完整居中，头顶留适当空间，不要裁切人物。"
        else:
            style_hint = "横构图，主体完整居中，左右留适当空间，不要裁切人物。"

        return (
            f"{scene.image_prompt}\n"
            f"画面描述：{scene.visual}\n"
            f"{style_hint}\n"
            "限制：画面中绝对不要出现任何文字、字母、数字、符号、字幕、logo、水印、二维码。"
        )

    # ---- 方式 2：精确像素尺寸（必须满足总像素≥3686400，宽高比∈[1/16,16]）----
    # 各模板在不同朝向下的目标尺寸
    _SIZE_MAP: dict[tuple[str, str], tuple[int, int]] = {
        # image_full：匹配视频帧比例
        ("full", "portrait"):  (1440, 2560),   # 9:16,  3,686,400 px
        ("full", "landscape"): (2560, 1440),   # 16:9,  3,686,400 px
        # image_elegant：竖卡片
        ("card_portrait", "portrait"):  (1800, 2400),   # 3:4,  4,320,000 px
        ("card_portrait", "landscape"): (2400, 1800),   # 3:4,  4,320,000 px
        # image_card / modern / neon：横卡片
        ("card", "portrait"):  (2352, 1568),   # 3:2,  3,688,416 px
        ("card", "landscape"): (1568, 2352),   # 3:2,  3,688,416 px
    }

    def _size_for_template(self, video_w: int, video_h: int, template: str) -> str:
        """根据模板和视频朝向，返回 Seedream API 的 size 参数。"""
        from core.template_registry import get_image_size
        img_size = get_image_size(template) or "card"
        orientation = "landscape" if video_w > video_h else "portrait"
        key = (img_size, orientation)
        if key in self._SIZE_MAP:
            w, h = self._SIZE_MAP[key]
            return f"{w}x{h}"
        return self._size

    def _download_url(self, url: str, output_path: Path) -> None:
        with urlopen(url, timeout=self._timeout) as response:
            output_path.write_bytes(response.read())


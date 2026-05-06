"""图文推文生成管道：话题/初稿 → 知识库润色 → 插图 → 输出 MD。"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path

from core import prompts
from core.schema import Scene
from utils.file_utils import read_text, write_text

logger = logging.getLogger(__name__)


class TweetPipeline:
    """编排图文推文生成全流程。"""

    def __init__(self, retriever, model_manager, image_provider, config):
        self._retriever = retriever
        self._mgr = model_manager
        self._image_provider = image_provider
        self._cfg = config

    def run(
        self,
        *,
        topic: str | None = None,
        draft_path: str | None = None,
        feedback: str = "",
        output_path: str | None = None,
        no_images: bool = False,
    ) -> str:
        """生成图文推文，返回输出 MD 文件路径。"""
        if not topic and not draft_path:
            raise ValueError("必须提供 --topic 或 --draft 之一")

        logger.info("=" * 50)
        logger.info("TweetPipeline START: topic=%s draft=%s no_images=%s",
                     topic, draft_path, no_images)

        # 准备输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        label = topic or Path(draft_path).stem
        safe_label = "".join(c for c in label if c.isalnum() or c in "._- ")[:30].strip()
        job_dir = self._cfg.output_tweets_dir / f"{timestamp}_{safe_label}"
        image_dir = job_dir / "images"
        job_dir.mkdir(parents=True, exist_ok=True)

        # ---- Step 1: 检索知识库 ----
        t0 = time.time()
        logger.info("[1/5] Retrieving knowledge base ...")
        context = self._retrieve_context(topic, draft_path)
        logger.info("      -> context length=%d chars (%.1fs)", len(context), time.time() - t0)

        # ---- Step 2: AI 生成/润色推文 ----
        t0 = time.time()
        logger.info("[2/5] %s tweet ...", "Generating" if topic else "Polishing")
        article = self._generate_or_polish(topic=topic, draft_path=draft_path,
                                           feedback=feedback, context=context)
        logger.info("      -> article length=%d chars (%.1fs)", len(article), time.time() - t0)

        # ---- Step 3: AI 规划插图 ----
        image_plans = []
        if not no_images:
            t0 = time.time()
            logger.info("[3/5] Planning images ...")
            image_plans = self._plan_images(article)
            logger.info("      -> %d images planned (%.1fs)", len(image_plans), time.time() - t0)
        else:
            logger.info("[3/5] Skipped (--no-images)")

        # ---- Step 4: 生成图片 ----
        image_results = {}
        if image_plans and not no_images:
            t0 = time.time()
            logger.info("[4/5] Generating %d images ...", len(image_plans))
            image_dir.mkdir(parents=True, exist_ok=True)
            image_results = self._generate_images(image_plans, image_dir)
            logger.info("      -> %d/%d images generated (%.1fs)",
                        len(image_results), len(image_plans), time.time() - t0)
        else:
            logger.info("[4/5] Skipped")

        # ---- Step 5: 组装最终 MD ----
        logger.info("[5/5] Assembling final MD ...")
        final_md = self._assemble_md(article, image_plans, image_results)
        out_path = Path(output_path) if output_path else job_dir / "article.md"
        write_text(out_path, final_md)
        logger.info("      -> saved: %s", out_path)

        # 同时保存纯文本版本
        write_text(job_dir / "article_raw.md", article)

        logger.info("TweetPipeline DONE: %s (%d images)", out_path, len(image_results))
        return str(out_path)

    def _retrieve_context(self, topic: str | None, draft_path: str | None) -> str:
        """检索知识库，返回上下文文本。"""
        if topic:
            query = topic
        else:
            draft = read_text(draft_path)
            # 从初稿提取关键词
            kw_response = self._mgr.generate(
                "summarizer",
                prompts.EXTRACT_KEYWORDS_PROMPT.format(text=draft[:2000]),
            )
            keywords = [kw.strip() for kw in kw_response.replace("，", ",").split(",") if kw.strip()]
            query = keywords[0] if keywords else draft[:100]

        docs = self._retriever.retrieve(query, top_k=self._cfg.retrieval_top_k)
        if not docs:
            logger.warning("No relevant documents found for: %s", query[:50])
            return ""

        return "\n\n---\n\n".join(
            f"【来源 {d['metadata'].get('source_name', '?')}】\n{d['text']}"
            for d in docs
        )

    def _generate_or_polish(
        self, *, topic: str | None, draft_path: str | None,
        feedback: str, context: str,
    ) -> str:
        """生成或润色推文正文。"""
        context_block = context if context else "（知识库中暂无相关资料）"

        if topic:
            # 话题模式：从零生成
            user_prompt = prompts.GENERATE_TWEET.format(
                topic=topic,
                context=context_block,
            )
        else:
            # 初稿模式：润色
            draft = read_text(draft_path)
            feedback_section = f"修改意见：{feedback}" if feedback else ""
            user_prompt = prompts.POLISH_TWEET.format(
                draft=draft,
                context=context_block,
                feedback_section=feedback_section,
            )

        return self._mgr.generate(
            "script_writer",
            user_prompt,
            system_prompt=prompts.SYSTEM_TWEET_WRITER,
        )

    def _plan_images(self, article: str) -> list[dict]:
        """AI 规划哪些段落需要配图。"""
        prompt = prompts.PLAN_TWEET_IMAGES.format(article=article[:4000])
        response = self._mgr.generate(
            "summarizer",
            prompt,
        )
        return self._parse_image_plans(response)

    def _parse_image_plans(self, text: str) -> list[dict]:
        """解析 AI 返回的插图规划 JSON。"""
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        start = text.find("[")
        end = text.rfind("]")
        if start < 0 or end < start:
            logger.warning("No JSON array found in image plan response")
            return []
        try:
            plans = json.loads(text[start:end + 1])
            if isinstance(plans, list):
                return [p for p in plans if isinstance(p, dict) and "paragraph_index" in p]
        except json.JSONDecodeError:
            logger.warning("Failed to parse image plan JSON")
        return []

    def _generate_images(self, plans: list[dict], image_dir: Path) -> dict[int, str]:
        """逐张生成图片，返回 {paragraph_index: relative_path}。"""
        results = {}
        for i, plan in enumerate(plans, start=1):
            para_idx = plan.get("paragraph_index", i)
            prompt = plan.get("image_prompt", "")
            if not prompt:
                continue
            try:
                pseudo_scene = Scene(
                    index=i,
                    subtitle="",
                    narration="",
                    visual=prompt,
                    image_prompt=prompt,
                    duration=5.0,
                )
                asset = self._image_provider.generate(
                    pseudo_scene, image_dir,
                    width=1024, height=1024,
                )
                rel_path = f"images/{Path(asset.path).name}"
                results[para_idx] = rel_path
                logger.info("      image %d/%d: para=%d -> %s", i, len(plans), para_idx, rel_path)
            except Exception as exc:
                logger.warning("      image %d FAILED: %s", i, exc)
        return results

    def _assemble_md(self, article: str, plans: list[dict], images: dict[int, str]) -> str:
        """在推文段落间插入图片引用，组装最终 MD。"""
        paragraphs = article.split("\n\n")
        lines = []

        for idx, para in enumerate(paragraphs):
            lines.append(para)
            # 检查该段落后是否需要插图
            if idx in images:
                # 从 plans 中找对应的 image_prompt 作为 alt text
                alt = ""
                for plan in plans:
                    if plan.get("paragraph_index") == idx:
                        alt = plan.get("image_prompt", "")
                        break
                lines.append("")
                lines.append(f"![{alt}]({images[idx]})")

        return "\n\n".join(lines)

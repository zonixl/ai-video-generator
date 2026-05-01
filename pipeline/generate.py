"""文案生成管道：话题 → 检索知识库 → LLM生成 → 保存。"""

import logging
import time
from pathlib import Path
from datetime import datetime

from core import prompts
from utils.file_utils import save_script, write_text

logger = logging.getLogger(__name__)


class GeneratePipeline:
    """编排文案生成全流程。"""

    def __init__(self, retriever, model_manager, config):
        self._retriever = retriever
        self._mgr = model_manager
        self._cfg = config

    def run(self, topic: str, style: str = "专业但不枯燥，适合短视频口播") -> str:
        """根据话题生成文案。"""
        logger.info("=" * 50)
        logger.info("GeneratePipeline START: topic='%s' style='%s'", topic, style)

        # ---- Step 1: 检索 ----
        t0 = time.time()
        logger.info("[1/3] Retrieving: '%s'", topic)
        docs = self._retriever.retrieve(topic, top_k=self._cfg.retrieval_top_k)
        logger.info("      -> %d docs found (%.1fs)", len(docs), time.time() - t0)
        for i, doc in enumerate(docs):
            text_preview = doc["text"][:80].replace("\n", " ")
            logger.debug("      [%d] score=%.4f source=%s | %s...",
                        i + 1, doc["score"],
                        doc["metadata"].get("source_name", "?"),
                        text_preview)
        if not docs:
            logger.warning("No relevant documents found for topic: '%s'", topic)

        # ---- Step 2: 构建上下文 + LLM生成 ----
        t0 = time.time()
        logger.info("[2/3] Building context + generating script (model=script_writer) ...")
        context = "\n\n---\n\n".join(
            f"【来源 {d['metadata'].get('source_name', '?')}】\n{d['text']}"
            for d in docs
        )

        user_prompt = prompts.GENERATE_SCRIPT.format(
            topic=topic,
            style=style,
            context=context if context else "（知识库中暂无相关资料）"
        )
        logger.debug("Prompt length: %d chars", len(user_prompt))

        script = self._mgr.generate(
            "script_writer",
            user_prompt,
            system_prompt=prompts.SYSTEM_SCRIPT_WRITER,
        )
        logger.info("      -> script generated: %d chars (%.1fs)", len(script), time.time() - t0)

        # ---- Step 3: 保存 ----
        logger.info("[3/3] Saving script ...")
        save_path = save_script(script, topic, self._cfg.output_scripts_dir)
        logger.info("      -> saved: %s", save_path.name)

        logger.info("GeneratePipeline DONE: %d chars -> %s", len(script), save_path.name)
        return script

    def polish(self, draft: str, feedback: str) -> str:
        """润色文案：AI提取关键词 → 检索知识库 → 有资料则结合润色，无则直接润色。"""
        logger.info("Polishing: feedback='%s' draft_len=%d", feedback, len(draft))
        t0 = time.time()

        # Step 1: 从文案提取关键词
        logger.info("  [1/3] Extracting keywords from draft ...")
        kw_prompt = prompts.EXTRACT_KEYWORDS_PROMPT.format(text=draft[:2000])
        kw_response = self._mgr.generate("summarizer", kw_prompt)
        keywords = [kw.strip() for kw in kw_response.replace("，", ",").split(",") if kw.strip()]
        logger.info("  -> keywords: %s", keywords)

        # Step 2: 用关键词检索知识库
        context = ""
        if keywords:
            logger.info("  [2/3] Searching knowledge base with keywords ...")
            all_docs = []
            seen_ids = set()
            for kw in keywords[:3]:  # 最多用3个关键词检索
                docs = self._retriever.retrieve(kw, top_k=3)
                for doc in docs:
                    if doc["id"] not in seen_ids:
                        seen_ids.add(doc["id"])
                        all_docs.append(doc)
            logger.info("  -> %d relevant docs found", len(all_docs))

            if all_docs:
                context = "\n\n---\n\n".join(
                    f"【来源 {d['metadata'].get('source_name', '?')}】\n{d['text']}"
                    for d in all_docs[:5]
                )

        # Step 3: 润色（有资料 vs 无资料）
        logger.info("  [3/3] Polishing%s ...", " with KB context" if context else " directly")
        if context:
            user_prompt = prompts.POLISH_SCRIPT_WITH_CONTEXT.format(
                draft=draft, feedback=feedback, context=context
            )
        else:
            user_prompt = prompts.POLISH_SCRIPT.format(draft=draft, feedback=feedback)

        polished = self._mgr.generate(
            "polisher", user_prompt, system_prompt=prompts.SYSTEM_POLISHER,
        )
        logger.info("Polished: %d -> %d chars (%.1fs)", len(draft), len(polished), time.time() - t0)
        return polished

    def polish_to_file(self, draft_path: str, feedback: str) -> str:
        """从文件读取原文案，润色后保存为新文件。"""
        from utils.file_utils import read_text

        draft = read_text(draft_path)
        polished = self.polish(draft, feedback)

        output_dir = self._cfg.output_scripts_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = Path(output_dir) / f"polished_{timestamp}.md"
        write_text(out_path, polished)
        logger.info("Polished script saved: %s", out_path)
        return polished

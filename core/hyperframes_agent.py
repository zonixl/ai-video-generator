"""Agent orchestration for safe HyperFrames file generation."""

from __future__ import annotations

import json
import logging
import re

from core import prompts
from core.hyperframes_schema import (
    HyperframesAgentPlan,
    HyperframesFile,
    HyperframesJob,
    HyperframesVideoRequest,
    plan_from_dict,
)
from core.hyperframes_sandbox import HyperframesSandbox

logger = logging.getLogger(__name__)


class HyperframesVideoAgent:
    def __init__(self, *, model_manager=None, instance_name: str = "remotion_designer"):
        self._model_manager = model_manager
        self._instance_name = instance_name

    def generate(
        self,
        request: HyperframesVideoRequest,
        *,
        job: HyperframesJob,
        sandbox: HyperframesSandbox,
        renderer=None,
    ) -> tuple[HyperframesAgentPlan, bool]:
        if request.use_agents_sdk:
            try:
                return self._generate_with_agents_sdk(request, job=job, sandbox=sandbox, renderer=renderer)
            except ImportError:
                logger.warning("OpenAI Agents SDK is not installed; falling back to ModelManager/rule generation.")
            except Exception:
                logger.warning("Agents SDK generation failed; falling back to ModelManager/rule generation.", exc_info=True)
        return self._generate_without_sdk(request), False

    def _generate_with_agents_sdk(
        self,
        request: HyperframesVideoRequest,
        *,
        job: HyperframesJob,
        sandbox: HyperframesSandbox,
        renderer=None,
    ) -> tuple[HyperframesAgentPlan, bool]:
        from agents import Agent, Runner, function_tool

        @function_tool
        def write_file(path: str, content: str) -> str:
            target = sandbox.write_file(job, path, content)
            return f"wrote {target.relative_to(job.workspace_dir).as_posix()}"

        @function_tool
        def read_file(path: str) -> str:
            return sandbox.read_file(job, path)

        @function_tool
        def list_files() -> list[str]:
            return sandbox.list_files(job)

        @function_tool
        def lint_hyperframes() -> str:
            if renderer is None:
                return "renderer is not configured"
            log = renderer.lint(job)
            return str(log)

        instructions = prompts.SYSTEM_HYPERFRAMES_AGENT
        agent = Agent(
            name="HyperFramesVideoAgent",
            instructions=instructions,
            tools=[write_file, read_file, list_files, lint_hyperframes],
        )
        result = Runner.run_sync(agent, self._prompt(request), max_turns=8)
        files = [
            HyperframesFile(path=path, content=sandbox.read_file(job, path))
            for path in sandbox.list_files(job)
            if path.rsplit(".", 1)[-1].lower() in {"html", "css", "js", "json", "txt", "svg"}
        ]
        if not files or not _validate_hyperframes_files(files):
            text = getattr(result, "final_output", "") or ""
            return self._parse_or_rule(text, request), False
        return HyperframesAgentPlan(files=files, notes=str(getattr(result, "final_output", ""))[:1000]), True

    def _generate_without_sdk(self, request: HyperframesVideoRequest) -> HyperframesAgentPlan:
        if self._model_manager is not None:
            try:
                response = self._model_manager.generate(
                    self._instance_name,
                    self._prompt(request),
                    system_prompt=prompts.SYSTEM_HYPERFRAMES_AGENT,
                )
                return self._parse_or_rule(response, request)
            except Exception:
                logger.warning("ModelManager HyperFrames generation failed; using rule-based starter.", exc_info=True)
        return self._rule_based_plan(request)

    def _parse_or_rule(self, response: str, request: HyperframesVideoRequest) -> HyperframesAgentPlan:
        try:
            data = json.loads(_extract_json(response))
            plan = plan_from_dict(data)
            if plan.files and _validate_hyperframes_files(plan.files):
                return plan
            if plan.files:
                logger.warning("LLM output missing required HyperFrames attributes; using rule-based starter.")
        except Exception:
            logger.warning("Could not parse HyperFrames agent JSON; using rule-based starter.", exc_info=True)
        return self._rule_based_plan(request)

    def _prompt(self, request: HyperframesVideoRequest) -> str:
        width, height = _dimensions_for_ratio(request.ratio)
        return prompts.PLAN_HYPERFRAMES_VIDEO.format(
            title=request.title or "Tech Video",
            duration=request.duration,
            ratio=request.ratio,
            fps=request.fps,
            style=request.style,
            script=request.script,
            width=width,
            height=height,
        )

    def _rule_based_plan(self, request: HyperframesVideoRequest) -> HyperframesAgentPlan:
        title = _escape_html(request.title or _first_line(request.script) or "AI Workflow")
        lines = [_escape_html(item) for item in _split_script(request.script)]
        duration = max(5, min(30, int(request.duration)))
        width, height = _dimensions_for_ratio(request.ratio)
        ratio_class = request.ratio.replace(":", "-")
        phrases = "".join(
            f'<span id="phrase-{index + 1}" class="clip phrase" data-start="{1.6 + index * 0.7:.1f}" data-duration="{max(1.4, duration - 2.8 - index * 0.35):.1f}" data-track-index="{index + 2}">{line}</span>'
            for index, line in enumerate(lines[:5])
        )
        index_html = f"""<!doctype html>
<html lang="zh-CN" data-duration="{duration}" data-fps="{int(request.fps)}" data-ratio="{request.ratio}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="./styles.css" />
  <script src="https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js"></script>
</head>
<body class="ratio-{ratio_class}">
  <main
    id="root"
    class="stage clip"
    data-composition-id="main"
    data-start="0"
    data-duration="{duration}"
    data-width="{width}"
    data-height="{height}"
    data-fps="{int(request.fps)}"
    data-track-index="0"
  >
    <div class="grid"></div>
    <div class="scan"></div>
    <section id="hero-panel" class="hero clip" data-start="0.2" data-duration="{duration - 0.4:.1f}" data-track-index="1">
      <p class="eyebrow">AUTOMATED INTELLIGENCE</p>
      <h1>{title}</h1>
      <div class="hud">
        <div class="meter"><i></i></div>
        <div class="readout">SYSTEM READY</div>
      </div>
    </section>
    <section class="phrases">{phrases}</section>
    <div class="orb orb-a"></div>
    <div class="orb orb-b"></div>
    <div id="main-caption" class="caption clip" data-start="0.4" data-duration="{duration - 0.8:.1f}" data-track-index="9">{lines[0] if lines else title}</div>
  </main>
  <script src="./timeline.js"></script>
</body>
</html>
"""
        styles_css = """*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#030712;color:#e5f7ff;font-family:"Microsoft YaHei",Arial,sans-serif}.stage{position:relative;width:100vw;height:100vh;overflow:hidden;background:radial-gradient(circle at 18% 22%,rgba(56,189,248,.35),transparent 28%),radial-gradient(circle at 82% 18%,rgba(99,102,241,.28),transparent 30%),linear-gradient(135deg,#020617,#07111f 58%,#0b1022)}.grid{position:absolute;inset:-2%;background-image:linear-gradient(rgba(125,211,252,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(125,211,252,.12) 1px,transparent 1px);background-size:44px 44px;transform:perspective(900px) rotateX(54deg) translateY(12%);transform-origin:bottom;opacity:.75;animation:gridShift 8s linear infinite}.scan{position:absolute;inset:0;background:linear-gradient(180deg,transparent,rgba(56,189,248,.16),transparent);height:24%;animation:scan 4s linear infinite}.hero{position:absolute;left:9%;right:9%;top:11%;padding:32px 34px;border:1px solid rgba(125,211,252,.38);background:linear-gradient(135deg,rgba(15,23,42,.82),rgba(8,47,73,.42));box-shadow:0 0 45px rgba(14,165,233,.22),inset 0 0 40px rgba(56,189,248,.08);clip-path:polygon(0 0,94% 0,100% 18%,100% 100%,6% 100%,0 82%);animation:panelIn .8s ease-out both}.eyebrow{margin:0 0 12px;color:#67e8f9;letter-spacing:3px;font-size:18px;font-weight:800}.hero h1{margin:0;font-size:64px;line-height:1.05;color:#f8fbff;text-shadow:0 0 18px rgba(56,189,248,.55)}.hud{display:flex;align-items:center;gap:18px;margin-top:26px}.meter{width:46%;height:8px;border:1px solid rgba(103,232,249,.55);padding:1px}.meter i{display:block;height:100%;width:72%;background:linear-gradient(90deg,#22d3ee,#a78bfa);animation:meter 2.2s ease-in-out infinite}.readout{font-size:18px;color:#bae6fd}.phrases{position:absolute;left:10%;right:10%;top:47%;display:grid;gap:18px}.phrase{display:block;padding:18px 22px;border-left:4px solid #22d3ee;background:rgba(2,6,23,.58);box-shadow:0 0 24px rgba(56,189,248,.12);font-size:30px;font-weight:800;color:#dcf7ff;animation:phraseIn .7s ease-out both}.phrase:nth-child(2){animation-delay:.25s}.phrase:nth-child(3){animation-delay:.5s}.phrase:nth-child(4){animation-delay:.75s}.phrase:nth-child(5){animation-delay:1s}.orb{position:absolute;border-radius:50%;filter:blur(2px);opacity:.55;animation:pulse 4.4s ease-in-out infinite alternate}.orb-a{width:220px;height:220px;right:9%;bottom:13%;background:radial-gradient(circle,#38bdf8,transparent 62%)}.orb-b{width:160px;height:160px;left:4%;bottom:8%;background:radial-gradient(circle,#a78bfa,transparent 64%)}.caption{position:absolute;left:8%;right:8%;bottom:6%;font-size:34px;font-weight:900;text-align:center;color:#fff;text-shadow:0 3px 0 #000,0 0 14px rgba(56,189,248,.75);animation:captionIn .7s ease-out both}@keyframes scan{0%{transform:translateY(-120%)}100%{transform:translateY(520%)}}@keyframes gridShift{0%{background-position:0 0,0 0}100%{background-position:0 52px,52px 0}}@keyframes panelIn{from{opacity:0;transform:translateY(-20px) scale(.98)}to{opacity:1;transform:none}}@keyframes phraseIn{from{opacity:0;transform:translateY(18px)}to{opacity:1;transform:none}}@keyframes captionIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}@keyframes meter{50%{width:92%}}@keyframes pulse{to{transform:scale(1.08);opacity:.8}}@media (orientation:landscape){.hero{left:8%;right:42%;top:14%}.phrases{left:52%;right:7%;top:20%}.hero h1{font-size:56px}.caption{font-size:30px}}"""
        phrase_anims = "\n".join(
            f'  tl.from(".phrase:nth-child({idx + 1})", {{ opacity: 0, y: 18, duration: 0.5 }}, {1.6 + idx * 0.7:.1f});'
            for idx in range(min(len(lines[:5]), 5))
        )
        timeline_js = f"""window.hyperframesProject = {{name: "safe-tech-video", version: "1.0.0"}};
window.__timelines = window.__timelines || {{}};
var tl = gsap.timeline({{ paused: true }});
tl.from("#hero-panel", {{ opacity: 0, y: -20, duration: 0.8 }}, 0.2);
{phrase_anims}
tl.from("#main-caption", {{ opacity: 0, y: 14, duration: 0.7 }}, 0.4);
window.__timelines["main"] = tl;
"""
        meta_json = f'{{"compositionId":"main","width":{width},"height":{height},"duration":{duration},"fps":{int(request.fps)}}}\n'
        return HyperframesAgentPlan(
            files=[
                HyperframesFile("index.html", index_html),
                HyperframesFile("styles.css", styles_css),
                HyperframesFile("timeline.js", timeline_js),
                HyperframesFile("meta.json", meta_json),
            ],
            notes="Rule-based safe HyperFrames starter.",
        )


def _validate_hyperframes_files(files: list[HyperframesFile]) -> bool:
    """检查生成的文件是否满足 HyperFrames 最低要求。"""
    html_content = None
    js_content = None
    for f in files:
        if f.path.endswith(".html"):
            html_content = f.content
        if f.path.endswith(".js"):
            js_content = f.content

    if not html_content:
        return False

    required_attrs = ["data-composition-id", "data-width", "data-height"]
    for attr in required_attrs:
        if attr not in html_content:
            return False

    if "gsap" not in html_content.lower():
        return False

    if js_content and ("__timelines" not in js_content or "gsap.timeline" not in js_content):
        return False

    return True


def _extract_json(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("No JSON object found")
    return text[start:end + 1]


def _first_line(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:24]
    return ""


def _split_script(text: str) -> list[str]:
    parts = re.split(r"[。！？!?；;\n]+", text)
    clean = [part.strip() for part in parts if part.strip()]
    return clean or [text.strip()[:30] or "科技感自动生成视频"]


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _dimensions_for_ratio(ratio: str) -> tuple[int, int]:
    if ratio == "16:9":
        return 1920, 1080
    if ratio == "1:1":
        return 1080, 1080
    return 1080, 1920

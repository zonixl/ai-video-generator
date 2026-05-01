"""语音识别模块测试。"""

import pytest


@pytest.mark.skip(reason="需要GPU和模型文件，仅手动执行")
def test_transcribe():
    from core.stt import SpeechToText

    stt = SpeechToText(model_size="tiny", device="cpu", compute_type="int8")
    segments = stt.transcribe("test.mp3")

    assert len(segments) > 0
    for seg in segments:
        assert "text" in seg
        assert "start" in seg
        assert "end" in seg
        assert isinstance(seg["text"], str)

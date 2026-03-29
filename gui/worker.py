"""QThread worker – runs BeatConverter.convert() off the main thread."""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PySide6.QtCore import QThread, Signal
from backend.processor import BeatConverter

# Steps emitted during conversion (percent, message)
_STEPS = [
    ( 8,  "📂 Đọc file beat…"),
    (20,  "🎵 Phân tích BPM và nhịp…"),
    (35,  "⏱  Chuẩn hoá tempo…"),
    (52,  "🎛️  Áp dụng EQ & dynamics…"),
    (68,  "🔊 Xử lý hiệu ứng style…"),
    (82,  "🎹 Giả lập amp / organ…"),
    (92,  "✨ Normalize & export…"),
]

_converter = BeatConverter()   # singleton — reuse across jobs


class ConvertWorker(QThread):
    """
    Signals:
        progress(int pct, str message)
        finished(dict info)
        error(str message)
    """
    progress = Signal(int, str)
    finished = Signal(dict)
    error    = Signal(str)

    def __init__(self, input_path: str, output_path: str,
                 style: str, intensity: float, parent=None):
        super().__init__(parent)
        self._in   = input_path
        self._out  = output_path
        self._style = style
        self._ix    = intensity

    def run(self):
        # Emit fake progress ticks while real work runs
        # (processor is synchronous; we interleave with QTimer-less approach)
        import threading, time

        done = threading.Event()
        result: dict = {}

        def _work():
            try:
                info = _converter.convert(self._in, self._out, self._style, self._ix)
                result["info"] = info
            except Exception as e:
                result["error"] = str(e)
            finally:
                done.set()

        thread = threading.Thread(target=_work, daemon=True)
        thread.start()

        for pct, msg in _STEPS:
            if done.is_set():
                break
            self.progress.emit(pct, msg)
            done.wait(timeout=1.2)

        done.wait()   # block until done

        if "error" in result:
            self.error.emit(result["error"])
        else:
            self.progress.emit(100, "✅ Hoàn thành!")
            self.finished.emit(result["info"])

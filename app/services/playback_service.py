from __future__ import annotations

import sounddevice as sd


class PlaybackService:
    def play(self, audio, sample_rate: int) -> None:
        sd.stop()
        sd.play(audio, samplerate=sample_rate)

    def stop(self) -> None:
        sd.stop()

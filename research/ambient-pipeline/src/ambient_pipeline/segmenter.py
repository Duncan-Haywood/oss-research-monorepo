"""Turn per-frame speech probabilities into utterance segments (pure Python, no models).

A hysteresis state machine: speech starts when the probability reaches `on`, and the
utterance ends after `hangover_ms` of consecutive frames below `off`. The hangover is the
largest single term in the reply-latency budget, so it is explicit and tested.
"""
from dataclasses import dataclass
from typing import Iterable, Iterator, List

FRAME = 512   # samples per VAD frame at 16 kHz
SR = 16000
FRAME_MS = 1000.0 * FRAME / SR  # 32 ms


@dataclass
class Segment:
    start_frame: int
    end_frame: int          # exclusive; includes the trailing hangover frames
    speech_end_frame: int   # exclusive; last frame at or above `off`, plus one

    @property
    def start_s(self) -> float:
        return self.start_frame * FRAME / SR

    @property
    def end_s(self) -> float:
        return self.end_frame * FRAME / SR


class Segmenter:
    def __init__(self, on: float = 0.5, off: float = 0.35, hangover_ms: float = 500.0,
                 min_speech_ms: float = 160.0, pad_frames: int = 3):
        self.on, self.off = on, off
        self.hang = max(1, round(hangover_ms / FRAME_MS))
        self.min_speech = max(1, round(min_speech_ms / FRAME_MS))
        self.pad = pad_frames
        self._i = 0
        self._start = None
        self._last_speech = None
        self._quiet = 0

    def push(self, p: float):
        """Feed one frame probability. Returns a Segment when an utterance just closed."""
        i = self._i
        self._i += 1
        if self._start is None:
            if p >= self.on:
                self._start = max(0, i - self.pad)
                self._first_speech = i
                self._last_speech = i
                self._quiet = 0
            return None
        if p >= self.off:
            self._last_speech = i
            self._quiet = 0
            return None
        self._quiet += 1
        if self._quiet >= self.hang:
            seg = Segment(self._start, i + 1, self._last_speech + 1)
            ok = (self._last_speech + 1 - self._first_speech) >= self.min_speech
            self._start = None
            return seg if ok else None
        return None

    def flush(self):
        if self._start is None:
            return None
        seg = Segment(self._start, self._i, self._last_speech + 1)
        ok = (self._last_speech + 1 - self._first_speech) >= self.min_speech
        self._start = None
        return seg if ok else None


def segment_probs(probs: Iterable[float], **kw) -> List[Segment]:
    s = Segmenter(**kw)
    out = [x for x in (s.push(p) for p in probs) if x]
    f = s.flush()
    if f:
        out.append(f)
    return out

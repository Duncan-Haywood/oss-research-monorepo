"""Latency budget for a reply that starts after the user stops speaking.

All terms are in milliseconds. Terms are measured by experiments/run.py; this module only
adds them up and compares against a target gap.
"""
from dataclasses import dataclass, asdict

# Median gap between turns in conversation is about 200 ms across ten languages
# (Stivers et al., PNAS 2009, doi:10.1073/pnas.0903616106). Used here as the "natural" target.
NATURAL_GAP_MS = 200.0


@dataclass
class Budget:
    hangover_ms: float      # silence the VAD waits for before it declares end of speech
    asr_ms: float           # transcribe the finished segment
    llm_first_token_ms: float
    llm_first_chunk_ms: float  # time until the first speakable chunk (clause) exists
    tts_first_audio_ms: float  # synthesise the first chunk

    @property
    def total_ms(self) -> float:
        return self.hangover_ms + self.asr_ms + self.llm_first_chunk_ms + self.tts_first_audio_ms

    def over(self, target_ms: float = NATURAL_GAP_MS) -> float:
        return self.total_ms - target_ms

    def as_dict(self):
        d = asdict(self)
        d["total_ms"] = self.total_ms
        return d


def required_speedup(b: Budget, target_ms: float = NATURAL_GAP_MS) -> float:
    """Factor by which the compute terms (all but the hangover) must shrink to hit target,
    holding the hangover fixed. Infinite if the hangover alone exceeds the target."""
    compute = b.total_ms - b.hangover_ms
    room = target_ms - b.hangover_ms
    return float("inf") if room <= 0 else compute / room


def split_clauses(text: str):
    """Yield speakable chunks from a stream-ending string: split after . ! ? , ; :"""
    buf = ""
    for ch in text:
        buf += ch
        if ch in ".!?,;:" and len(buf.strip()) >= 12:
            yield buf.strip()
            buf = ""
    if buf.strip():
        yield buf.strip()


def first_chunk_ready(token_times_ms, token_texts, min_chars: int = 12):
    """Given per-token arrival times and texts, return (time_ms, chunk_text) when the first
    clause boundary arrives, or the final time if the text ends without one."""
    buf = ""
    for t, s in zip(token_times_ms, token_texts):
        buf += s
        if any(c in buf for c in ".!?,;:") and len(buf.strip()) >= min_chars:
            return t, buf.strip()
    return (token_times_ms[-1] if token_times_ms else 0.0), buf.strip()

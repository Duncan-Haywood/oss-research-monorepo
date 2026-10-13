import math
import unittest

from ambient_pipeline.budget import Budget, required_speedup, first_chunk_ready, split_clauses
from ambient_pipeline.segmenter import FRAME_MS, segment_probs


def frames(ms):
    return round(ms / FRAME_MS)


class SegmenterTests(unittest.TestCase):
    def test_single_utterance_with_hangover(self):
        probs = [0.0] * 10 + [0.9] * 30 + [0.0] * 40
        segs = segment_probs(probs, hangover_ms=320)
        self.assertEqual(len(segs), 1)
        s = segs[0]
        self.assertEqual(s.speech_end_frame, 40)
        # the segment closes hang frames after the last speech frame
        self.assertEqual(s.end_frame - s.speech_end_frame, round(320 / FRAME_MS))

    def test_short_pause_does_not_split(self):
        probs = [0.9] * 20 + [0.0] * 5 + [0.9] * 20 + [0.0] * 40
        self.assertEqual(len(segment_probs(probs, hangover_ms=500)), 1)

    def test_long_pause_splits(self):
        probs = [0.9] * 20 + [0.0] * 40 + [0.9] * 20 + [0.0] * 40
        self.assertEqual(len(segment_probs(probs, hangover_ms=500)), 2)

    def test_blip_rejected(self):
        probs = [0.0] * 5 + [0.9] * 2 + [0.0] * 40
        self.assertEqual(segment_probs(probs, min_speech_ms=160), [])

    def test_flush_closes_open_segment(self):
        probs = [0.0] * 3 + [0.9] * 20
        segs = segment_probs(probs)
        self.assertEqual(len(segs), 1)
        self.assertEqual(segs[0].end_frame, 23)

    def test_longer_hangover_delays_end(self):
        probs = [0.9] * 20 + [0.0] * 100
        a = segment_probs(probs, hangover_ms=200)[0]
        b = segment_probs(probs, hangover_ms=800)[0]
        self.assertLess(a.end_frame, b.end_frame)
        self.assertEqual(a.speech_end_frame, b.speech_end_frame)


class BudgetTests(unittest.TestCase):
    def test_total_and_over(self):
        b = Budget(hangover_ms=100, asr_ms=50, llm_first_token_ms=30, llm_first_chunk_ms=80, tts_first_audio_ms=40)
        self.assertEqual(b.total_ms, 270)  # first token is inside first chunk, not added twice
        self.assertEqual(b.over(200), 70)

    def test_required_speedup(self):
        b = Budget(100, 50, 30, 80, 40)
        self.assertAlmostEqual(required_speedup(b, 200), 170 / 100)
        self.assertTrue(math.isinf(required_speedup(Budget(300, 1, 1, 1, 1), 200)))

    def test_first_chunk(self):
        t, s = first_chunk_ready([10, 20, 30, 40], ["Sure", ",", " I can", " help."], min_chars=4)
        self.assertEqual((t, s), (20, "Sure,"))
        t, s = first_chunk_ready([10, 20], ["Hi", " there"])
        self.assertEqual((t, s), (20, "Hi there"))

    def test_split_clauses(self):
        self.assertEqual(list(split_clauses("Sure, I can help with that. Done")),
                         ["Sure, I can help with that.", "Done"])


if __name__ == "__main__":
    unittest.main()

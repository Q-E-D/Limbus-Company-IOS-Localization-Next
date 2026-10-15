"""Exact text fallbacks preserve controls and never become substring rewrites."""
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import prepare_release as p


class TextFallbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "fallbacks.json"

    def load(self, entries, charset=set("可複製以"), glyph_map=None):
        self.path.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
        return p.load_text_fallbacks(self.path, charset, glyph_map or {})

    def test_rejects_lost_placeholder_and_changed_rich_text_controls(self):
        for source, target in [("{0}，可以吗？", "可以？"),
                               ("<link=123>复制</link>", "複製")]:
            with self.subTest(source=source):
                with self.assertRaisesRegex(ValueError, "formatting controls"):
                    self.load({source: target})

    def test_rejects_uncovered_replacement_and_duplicate_source(self):
        with self.assertRaisesRegex(ValueError, "outside charset"):
            self.load({"可以吗？": "可以嗎？"})
        self.path.write_text('{"copy":"a","copy":"b"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            p.load_text_fallbacks(self.path, set(), {})

    def test_replacement_is_validated_after_character_fallback(self):
        entries = self.load({"copy": "复制"}, set("複製"), {ord("复"): "複", ord("制"): "製"})
        self.assertEqual(entries, {"copy": "复制"})

    def test_exact_visible_values_only_and_separate_counters(self):
        entries = self.load({"{0}，可以吗？": "{0}，可以？"})
        report = {"missing_chars": Counter(), "mapped_chars": Counter(),
                  "text_fallbacks_applied": Counter()}
        source = {"content": "{0}，可以吗？", "teller": "{0}，可以吗？",
                  "id": "{0}，可以吗？", "path": "{0}，可以吗？",
                  "text": "前面：{0}，可以吗？"}
        result = p.adapt_text(source, "", set("可複製以前面"), {}, report, entries)
        self.assertEqual(result["content"], "{0}，可以？")
        self.assertEqual(result["teller"], "{0}，可以？")
        for field in ("id", "path", "text"):
            self.assertEqual(result[field], source[field])
        self.assertEqual(report["text_fallbacks_applied"], {"{0}，可以吗？": 2})
        self.assertEqual(report["mapped_chars"], {})
        self.assertEqual(report["missing_chars"], {"吗": 1})

    def test_preserve_mode_rejects_text_fallbacks_before_reading_archives(self):
        with self.assertRaisesRegex(ValueError, "compatible mode"):
            p.build_overlay_from_llc(b"", b"", self.path.parent / "out", self.path,
                                     text_fallbacks_path=self.path)

    def test_reported_screenshot_values_have_covered_fallbacks(self):
        root = Path(__file__).resolve().parent
        charset = p.load_charset(root / "data/mobile-font-charset.txt")
        glyph_map = p.load_glyph_map(root / "data/mobile-safe-glyph-map.json", charset)
        entries = p.load_text_fallbacks(root / "data/mobile-text-fallbacks.json", charset, glyph_map)
        samples = [
            ("name", "复制", "複製"),
            ("content", "{0}，可以吗？", "{0}，可以？"),
            ("teller", "卡戎", "Charon"),
            ("content", "前面有障碍物。布隆布隆，可以吗？", "前面有障碍物。布隆布隆，可以？"),
            ("content", "毕竟，当你想战胜枯燥感时，没有比闭上双眼更高效的选择。",
             "畢竟，要克服枯燥感，没有比閉上双眼更高效的選擇。"),
            ("content", "嗯。哐哧哐哧。", "唔。轟隆轟隆。"),
        ]
        for field, source, expected in samples:
            with self.subTest(source=source):
                report = {"missing_chars": Counter(), "mapped_chars": Counter()}
                self.assertEqual(p.adapt_text(source, field, charset, glyph_map, report, entries),
                                 expected)
                self.assertEqual(report["missing_chars"], {})


if __name__ == "__main__":
    unittest.main()

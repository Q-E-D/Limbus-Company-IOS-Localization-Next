"""Conservative glyph fallback must not guess ambiguous or unrelated characters."""
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import build_glyph_map as g
import prepare_release as p


class GlyphMapTests(unittest.TestCase):
    def test_traditional_preferred_then_single_japanese_variant(self):
        mapping = g.build_map({"对": ["對"], "说": ["說"]},
                              {"對": ["対"], "說": ["説"]}, set("對対説"))
        self.assertEqual(mapping, {"对": "對", "说": "説"})

    def test_ambiguous_supported_and_uncovered_characters_are_not_guessed(self):
        mapping = g.build_map({"发": ["發", "髮"], "后": ["後"],
                               "吗": ["嗎"], "乡": ["鄉"]},
                              {"鄉": ["郷", "鄕"]}, set("發髮后後郷"))
        self.assertEqual(mapping, {})

    def test_pinned_dictionary_identity_required(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "STCharacters.txt"
            path.write_text("你\t袮\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                g.read_dictionary(path, "STCharacters.txt")

    def test_distributed_map_preserves_existing_simplified_and_unrelated_fields(self):
        root = Path(__file__).resolve().parent
        charset = p.load_charset(root / "data/mobile-font-charset.txt")
        mapping = p.load_glyph_map(root / "data/mobile-safe-glyph-map.json", charset)
        self.assertTrue(mapping)
        for source in "你发后里干吧":
            self.assertNotIn(ord(source), mapping)
        report = {"missing_chars": Counter(), "mapped_chars": Counter()}
        result = p.adapt_text({"text": "这对你说后里干吧", "id": "这", "path": "这"},
                              "", charset, mapping, report)
        self.assertEqual(result, {"text": "這對你説后里干吧", "id": "这", "path": "这"})
        self.assertIn("你", report["missing_chars"])
        self.assertEqual(report["mapped_chars"], {"这->這": 1, "对->對": 1, "说->説": 1})


if __name__ == "__main__":
    unittest.main()

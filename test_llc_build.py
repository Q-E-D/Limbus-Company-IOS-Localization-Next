"""Synthetic archive regressions for the LLC-to-iOS overlay boundary."""
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import prepare_release as p


def archive(entries):
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, data in entries.items():
            z.writestr(name, json.dumps(data, ensure_ascii=False))
    return result.getvalue()


class LLCBuildRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.charset = self.root / "charset.txt"
        self.charset.write_text("中文好甲乙名字称号新旧描述条件结果可见日原文", encoding="utf-8")
        self.glyph_map = self.root / "map.json"
        self.glyph_map.write_text('{"你":"好"}', encoding="utf-8")

    def build(self, jp, llc, **kwargs):
        output = self.root / "overlay"
        report = p.build_overlay_from_llc(
            archive(jp), archive(llc), output, self.charset,
            glyph_map_path=self.glyph_map, **kwargs)
        files = {str(path.relative_to(output)): json.loads(path.read_text())
                 for path in output.rglob("*.json")}
        return files, report

    def single(self, target, source, **kwargs):
        files, report = self.build(
            {"LocalizeTemp_jp/JP_Test.json": {"dataList": target}},
            {"LLC/Test.json": {"dataList": source}}, **kwargs)
        return files.get("JP_Test.json", {}).get("dataList"), report

    def test_rpg_inserted_key_does_not_shift_rows(self):
        rows, report = self.single(
            [{"key": "first", "name": "original first"},
             {"key": "second", "name": "original second"}],
            [{"key": "inserted", "name": "wrong"},
             {"key": "second", "name": "乙"},
             {"key": "first", "name": "甲"}])
        self.assertEqual(rows, [{"key": "first", "name": "甲"},
                                {"key": "second", "name": "乙"}])
        self.assertEqual(report["matched_rows"], 2)

    def test_nested_index_and_level_match_when_reordered(self):
        rows, _ = self.single(
            [{"id": 7, "name": "old", "variants": [
                {"index": 1, "levels": [{"level": 1, "desc": "old one"},
                                          {"level": 2, "desc": "old two"}]},
                {"index": 2, "name": "old second"}]}],
            [{"id": 7, "name": "新", "variants": [
                {"index": 2, "name": "乙"},
                {"index": 1, "levels": [{"level": 2, "desc": "乙"},
                                          {"level": 1, "desc": "甲"}]}]}])
        variants = rows[0]["variants"]
        self.assertEqual([r["index"] for r in variants], [1, 2])
        self.assertEqual(variants[0]["levels"],
                         [{"level": 1, "desc": "甲"}, {"level": 2, "desc": "乙"}])
        self.assertEqual(variants[1]["name"], "乙")

    def test_controls_and_unrecognized_fields_stay_original(self):
        controls = {"path": "jp/你", "type": "JP", "font": "original",
                    "voice": "voice-jp", "sprite": "original-sprite",
                    "unknown": "你", "condition": "original-condition"}
        rows, _ = self.single(
            [{"id": 1, "name": "old", **controls}],
            [{"id": 1, "name": "你", **{key: "changed" for key in controls}}],
            glyph_mode="compatible")
        self.assertEqual(rows[0], {"id": 1, "name": "好", **controls})

    def test_visible_fields_and_story_additions_are_adapted(self):
        rows, report = self.single(
            [{"id": 1, "model": "speaker", "content": "old",
              "goalDescription1": "old", "skinItemDesc": "old",
              "nameList": ["old"]}],
            [{"id": 1, "model": "speaker", "content": "你",
              "teller": "你", "title": "你", "goalDescription1": "你",
              "skinItemDesc": "你", "nameList": ["你"]}],
            glyph_mode="compatible")
        for field in ("content", "teller", "title", "goalDescription1", "skinItemDesc"):
            self.assertEqual(rows[0][field], "好")
        self.assertEqual(rows[0]["nameList"], ["好"])
        self.assertEqual(report["mapped_chars"], {"你->好": 6})
        self.assertEqual(report["missing_chars"], {})

    def test_default_preserve_reports_final_missing_glyph(self):
        rows, report = self.single([{"id": 1, "name": "old"}],
                                   [{"id": 1, "name": "你你"}])
        self.assertEqual(rows[0]["name"], "你你")
        self.assertEqual(report["glyph_mode"], "preserve")
        self.assertEqual(report["mapped_chars"], {})
        self.assertEqual(report["missing_chars"], {"你": 1})
        self.assertEqual(report["missing_glyph_examples"],
                         {"你": "LocalizeTemp_jp/JP_Test.json"})

    def test_exact_text_fallback_precedes_glyph_map_and_reports_unused_entries(self):
        path = self.root / "text-fallbacks.json"
        path.write_text('{"你":"中文","unused":"中文"}', encoding="utf-8")
        rows, report = self.single([{"id": 1, "name": "old"}],
                                   [{"id": 1, "name": "你"}],
                                   glyph_mode="compatible", text_fallbacks_path=path)
        self.assertEqual(rows[0]["name"], "中文")
        self.assertEqual(report["text_fallbacks_applied"], {"你": 1})
        self.assertEqual(report["mapped_chars"], {})
        self.assertEqual(report["missing_chars"], {})
        self.assertEqual(report["unused_text_fallbacks"], ["unused"])

    def test_positional_length_mismatch_and_unknown_arrays_are_preserved(self):
        rows, report = self.single(
            [{"id": 1, "name": "old", "options": [{"desc": "original"}],
              "unknownRows": [{"desc": "original unknown"}]}],
            [{"id": 1, "name": "新", "options": [{"desc": "甲"}, {"desc": "乙"}],
              "unknownRows": [{"desc": "wrong"}]}])
        self.assertEqual(rows[0]["options"], [{"desc": "original"}])
        self.assertEqual(rows[0]["unknownRows"], [{"desc": "original unknown"}])
        self.assertTrue(any("/options:" in path for path in report["unmerged_paths"]))
        self.assertTrue(any("/unknownRows:" in path for path in report["unmerged_paths"]))

    def test_duplicate_id_count_mismatch_is_not_guessed(self):
        rows, report = self.single(
            [{"id": 1, "name": "original one"}, {"id": 1, "name": "original two"},
             {"id": 2, "name": "old"}],
            [{"id": 1, "name": "wrong"}, {"id": 2, "name": "新"}])
        self.assertEqual([row["name"] for row in rows], ["original one", "original two", "新"])
        self.assertEqual(len(report["unmerged_paths"]), 2)

    def test_duplicate_llc_basename_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate resource basename"):
            self.build({"LocalizeTemp_jp/JP_Test.json": {"dataList": []}},
                       {"one/Test.json": {}, "two/Test.json": {}})

    def test_llc_expanded_limit_is_checked_before_parsing(self):
        jp = archive({"LocalizeTemp_jp/JP_Test.json": {"dataList": []}})
        llc = archive({"LLC/Test.json": {"padding": "x" * 2000}})
        with patch.object(p, "MAX_EXPANDED", 1000):
            with self.assertRaisesRegex(ValueError, "Archive expands beyond limit"):
                p.build_overlay_from_llc(jp, llc, self.root / "overlay", self.charset)

    def test_delta_backfill_and_speaker_names(self):
        story_path = "LocalizeTemp_jp/StoryData/JP_Story-a1c2p3.json"
        files, report = self.build(
            {story_path: {"dataList": [{"id": 10, "model": "model-one", "content": "old"}]},
             "LocalizeTemp_jp/JP_ScenarioModelCodes-AutoCreated.json": {
                 "dataList": [{"id": "model-one", "name": "old", "nickName": "old"}]}},
            {"LLC/Story.json": {"dataList": [
                {"id": 9, "model": "model-one", "content": "wrong"},
                {"id": 10, "model": "model-one", "content": "中文"}]},
             "LLC/ScenarioModelCodes-AutoCreated.json": {
                 "dataList": [{"id": "model-one", "name": "名字", "nickName": "称号"}]}})
        self.assertEqual(files["StoryData/JP_Story-a1c2p3.json"]["dataList"],
                         [{"id": 10, "model": "model-one", "content": "中文",
                           "teller": "名字", "title": "称号"}])
        self.assertEqual(report["backfilled_files"], ["Story-a1c2p3.json"])
        self.assertEqual(report["speaker_fields_added"], {"teller": 1, "title": 1})
        self.assertEqual(report["unknown_story_models"], {})


if __name__ == "__main__":
    unittest.main()

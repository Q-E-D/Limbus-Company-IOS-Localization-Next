"""Audit the final archive, not just the translated overlay."""
import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import prepare_release as p
from test_llc_build import archive


class OutputAuditTests(unittest.TestCase):
    def test_scans_untranslated_files_and_supplementary_cjk(self):
        data = archive({
            "LocalizeTemp_jp/JP_Translated.json": {"dataList": [{"id": 1, "text": "中文"}]},
            "LocalizeTemp_jp/StoryData/JP_New.json": {"dataList": [
                {"id": 2, "model": "你", "text": "你你𫚉", "unknown": "未"}]}})
        report = p.audit_output_text(data, set("中文"))
        self.assertEqual(report["visible_fields"], 2)
        self.assertEqual(report["missing_chars"], {"你": 1, "𫚉": 1})
        self.assertEqual(report["examples"]["missing_chars"]["你"]["pointer"], "/dataList/0/text")
        self.assertEqual(report["examples"]["missing_chars"]["你"]["file"],
                         "LocalizeTemp_jp/StoryData/JP_New.json")

    def test_candidates_exclude_markup_and_placeholders_but_preserve_text(self):
        report = p.audit_output_text(archive({"LocalizeTemp_jp/JP_Test.json": {"dataList": [
            {"id": "english-key", "text": '<color=red>{player}</color>中文'},
            {"id": 2, "teller": "Gregor"},
            {"id": 3, "text": "こんにちは"},
            {"id": 4, "text": '<这是中文>English'}]}}), set("中文这是"))
        self.assertEqual(report["latin_candidate_fields"], 2)
        self.assertEqual(report["kana_candidate_fields"], 1)
        self.assertEqual(report["examples"]["latin_candidates"][0]["text"], "Gregor")
        self.assertEqual(report["missing_chars"], {})

    def test_candidate_examples_are_bounded_while_counts_remain_complete(self):
        report = p.audit_output_text(archive({"LocalizeTemp_jp/JP_Test.json": {
            "dataList": [{"id": i, "text": "English " + str(i)} for i in range(30)]}}), set("中"))
        self.assertEqual(report["latin_candidate_fields"], 30)
        self.assertEqual(len(report["examples"]["latin_candidates"]), 20)

    def test_repeated_names_do_not_hide_other_candidate_examples(self):
        data = archive({"LocalizeTemp_jp/JP_Test.json": {"dataList": [
            {"id": i, "text": "Gregor"} for i in range(30)] + [
            {"id": 30, "text": "English sentence"}]}})
        report = p.audit_output_text(data, set("中"), include_candidates=True)
        self.assertEqual([s["text"] for s in report["examples"]["latin_candidates"]],
                         ["Gregor", "English sentence"])
        self.assertEqual(len(report["candidate_locations"]["latin_candidates"]), 31)

    def test_cli_rejects_uncovered_jp_only_slot_after_successful_llc_merge(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            jp = archive({"LocalizeTemp_jp/JP_Test.json": {"dataList": [{"id": 1, "text": "中"}]},
                          "LocalizeTemp_jp/JP_Untranslated.json": {"dataList": [{"id": 2, "text": "𫚉"}]}})
            llc = archive({"LLC/Test.json": {"dataList": [{"id": 1, "text": "中"}]}})
            with zipfile.ZipFile(io.BytesIO(jp)) as z:
                files = {p.PREFIX + "jp/" + name.removeprefix("LocalizeTemp_jp/"):
                         {"Hash": p.game_hash(z.read(name)), "Size": len(z.read(name)), "Crc": 0}
                         for name in z.namelist()}
            manifest = json.dumps({"Version": "test", "EncryptKey": "", "EncryptIV": "",
                                   "Files": files, "SteamUpdateFiles": None}).encode()
            for name, content in [("jp.zip", jp), ("llc.zip", llc), ("manifest.json", manifest)]:
                (root / name).write_bytes(content)
            (root / "charset.txt").write_text("中", encoding="utf-8")
            argv = ["prepare_release.py", "--zip", str(root / "jp.zip"),
                    "--manifest", str(root / "manifest.json"),
                    "--zip-sha256", hashlib.sha256(jp).hexdigest(),
                    "--manifest-sha256", hashlib.sha256(manifest).hexdigest(),
                    "--llc-zip", str(root / "llc.zip"),
                    "--llc-zip-sha256", hashlib.sha256(llc).hexdigest(),
                    "--font-charset", str(root / "charset.txt"),
                    "--repo", "owner/repo", "--tag", "test", "--out", str(root / "out")]
            with patch("sys.argv", argv):
                with self.assertRaisesRegex(ValueError, "Uncovered final archive glyphs: 𫚉"):
                    p.main()
            self.assertFalse((root / "out").exists())


if __name__ == "__main__":
    unittest.main()

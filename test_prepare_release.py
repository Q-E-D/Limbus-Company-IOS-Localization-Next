import io
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

import prepare_release as p


class ReleaseTests(unittest.TestCase):
    def fixture(self, name="LocalizeTemp_jp/JP_Test.json", raw=b'{"text":"hello"}\r\n'):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr(name, raw)
        key = p.PREFIX + "jp/JP_Test.json"
        manifest = {"Version": "0.1", "EncryptKey": "preserved", "EncryptIV": "preserved",
                    "SteamUpdateFiles": None, "Files": {
                        key: {"Hash": p.game_hash(raw), "Size": len(raw), "Crc": 0}}}
        return data.getvalue(), json.dumps(manifest).encode()

    def test_hash_normalizes_crlf(self):
        self.assertEqual(p.game_hash(b"a\r\nb"), p.game_hash(b"a\nb"))

    def test_validate_rejects_wrong_game_hash(self):
        zip_data, manifest_data = self.fixture()
        manifest = json.loads(manifest_data)
        next(iter(manifest["Files"].values()))["Hash"] = "0" * 32
        with self.assertRaisesRegex(ValueError, "Game hash mismatch"):
            p.validate(zip_data, json.dumps(manifest).encode())

    def test_traversal_and_duplicate_json_rejected(self):
        zip_data, manifest_data = self.fixture("LocalizeTemp_jp/../JP_Test.json")
        with self.assertRaises(ValueError):
            p.validate(zip_data, manifest_data)
        with self.assertRaises(ValueError):
            p.parse_json(b'{"a":1,"a":2}')

    def test_overlay_rebuild_is_consistent_and_deterministic(self):
        zip_data, manifest_data = self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            overlay = Path(directory)
            replacement = '{"text":"測試"}\r\n'.encode()
            (overlay / "JP_Test.json").write_bytes(replacement)
            first = p.repack(zip_data, manifest_data, overlay)
            second = p.repack(zip_data, manifest_data, overlay)
        self.assertEqual(first, second)
        self.assertEqual(first[2], 1)
        self.assertEqual(p.validate(first[0], first[1])["zip_json_count"], 1)
        with zipfile.ZipFile(io.BytesIO(first[0])) as archive:
            self.assertEqual(archive.read("LocalizeTemp_jp/JP_Test.json"), replacement)

    def test_unknown_slot_rejected(self):
        zip_data, manifest_data = self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "JP_Unknown.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "No matching JP slot"):
                p.repack(zip_data, manifest_data, Path(directory))

    def test_module_limits_hosts_and_fixed_version(self):
        self.assertIn("github.com/a/repo", p.make_module("a/repo", "v1"))
        module = p.make_module("owner/repo", "reviewed-1")
        rule = module.split("[URL Rewrite]\n", 1)[1].splitlines()[0].split(" ", 1)[0]
        self.assertTrue(re.search(rule, "https://downloadcommon.limbuscompanycdn.org/a/localize_jp.zip?v=1"))
        self.assertFalse(re.search(rule, "https://other.example/localize_jp.zip"))
        self.assertFalse(re.search(rule, "https://downloadcommon.limbuscompanycdn.org/localize_jpXzip"))
        for repo, tag in [("owner/repo", "latest"), ("owner/repo", "v1\n[Script]")]:
            with self.assertRaises(ValueError):
                p.make_module(repo, tag)

    def test_sha_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "file"
            path.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                p.read_asset(path, "0" * 64)


if __name__ == "__main__":
    unittest.main()

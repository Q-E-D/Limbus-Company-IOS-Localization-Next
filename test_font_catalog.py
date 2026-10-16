"""Synthetic Addressables v2 directory fixtures with local/remote dependencies."""
import struct
import unittest

from inspect_font_catalog import Catalog, NULL, inspect_fonts


def fixture():
    data = bytearray(32)

    def value(*values):
        offset = len(data)
        data.extend(struct.pack("<" + "I" * len(values), *values))
        return offset

    def string(text, unicode=False):
        raw = text.encode("utf-16-le" if unicode else "ascii")
        value(len(raw))
        offset = len(data)
        data.extend(raw)
        return offset | (0x80000000 if unicode else 0)

    def array(*values):
        value(len(values) * 4)
        return value(*values)

    def location(name, internal, provider, deps=NULL):
        return value(string(name), internal, string(provider), deps, 0, NULL, NULL)

    tail = value(string("fonts.bundle"),
                 value(string("{UnityEngine.AddressableAssets.Addressables.RuntimePath}"), NULL)
                 | 0x40000000) | 0x40000000
    bundle = location("fonts.bundle", tail, "AssetBundleProvider")
    remote = location("scripts.bundle", string("https://example.com/scripts.bundle"),
                      "AssetBundleProvider")
    asset = location("Assets/Font/Fallback.asset", string("Assets/Font/Fallback.asset"),
                     "BundledAssetProvider", array(bundle, remote))
    locations = array(bundle, remote, asset)
    keys = array(0, locations, 0, locations)
    struct.pack_into("<8I", data, 0, 0x0DE38942, 2, keys, 0, 0, 0, 0, 0)
    return bytes(data)


class FontCatalogTests(unittest.TestCase):
    def test_dependency_paths_are_decoded_not_inferred_from_adjacent_strings(self):
        report = inspect_fonts(fixture())
        self.assertEqual(report["location_count"], 3)
        fonts = report["font_locations"]
        self.assertEqual(len(fonts), 2)
        asset = next(entry for entry in fonts if entry["primary_key"].endswith(".asset"))
        paths = [entry["internal_id"] for entry in asset["dependencies"]]
        self.assertEqual(paths, ["{UnityEngine.AddressableAssets.Addressables.RuntimePath}/fonts.bundle",
                                 "https://example.com/scripts.bundle"])

    def test_rejects_version_and_bounds_and_cyclic_strings(self):
        data = bytearray(fixture())
        struct.pack_into("<I", data, 4, 99)
        with self.assertRaisesRegex(ValueError, "version 2"):
            inspect_fonts(bytes(data))
        with self.assertRaisesRegex(ValueError, "bounds"):
            Catalog(fixture()).values(0xFFFFFFFF, 1)
        data = bytearray(fixture())
        offset = len(data)
        data.extend(struct.pack("<II", 36, offset | 0x40000000))
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            Catalog(bytes(data)).string(offset | 0x40000000)

    def test_unicode_string(self):
        data = bytearray(fixture())
        raw = "字体".encode("utf-16-le")
        data.extend(struct.pack("<I", len(raw)))
        offset = len(data)
        data.extend(raw)
        self.assertEqual(Catalog(bytes(data)).string(offset | 0x80000000), "字体")


if __name__ == "__main__":
    unittest.main()

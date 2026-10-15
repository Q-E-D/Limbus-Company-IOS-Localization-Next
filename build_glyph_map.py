#!/usr/bin/env python3
"""Build an opt-in glyph map from pinned OpenCC dictionaries, without networking.

Only single-target dictionary entries are eligible. The charset is an observed
reference, not a font cmap: this tool cannot establish actual device coverage.
"""
import argparse
import hashlib
import json
from pathlib import Path

from prepare_release import load_charset, require

OPENCC_COMMIT = "556ed22496d650bd0b13b6c163be9814637970ae"
DICTIONARY_SHA256 = {
    "STCharacters.txt": "ed1d268e0ad028511dcf5b0089faed0a980ad332449ec11d481ceefde6879f41",
    "JPVariants.txt": "db09543db11ffd42a2556070f3d0a8e2c0168726463bd5f8d530f3e54a5afab8",
}


def read_dictionary(path, name):
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == DICTIONARY_SHA256[name],
            f"Pinned OpenCC dictionary SHA-256 mismatch: {name}")
    result = {}
    for line in data.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        source, targets = line.split("\t")
        require(source not in result, f"Duplicate OpenCC entry: {source}")
        result[source] = targets.split(" ")
    return result


def build_map(simplified_to_traditional, japanese_variants, charset):
    result = {}
    for source, targets in sorted(simplified_to_traditional.items()):
        if len(source) != 1 or source in charset or len(targets) != 1:
            continue
        traditional = targets[0]
        if len(traditional) != 1:
            continue
        if traditional in charset:
            result[source] = traditional
            continue
        variants = japanese_variants.get(traditional, [])
        if len(variants) == 1 and len(variants[0]) == 1 and variants[0] in charset:
            result[source] = variants[0]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--st-characters", required=True, type=Path)
    parser.add_argument("--jp-variants", required=True, type=Path)
    parser.add_argument("--font-charset", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    mapping = build_map(read_dictionary(args.st_characters, "STCharacters.txt"),
                        read_dictionary(args.jp_variants, "JPVariants.txt"),
                        load_charset(args.font_charset))
    require(mapping, "No eligible glyph substitutions")
    with args.out.open("x", encoding="utf-8") as output:
        output.write(json.dumps(mapping, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"entries": len(mapping), "opencc_commit": OPENCC_COMMIT,
                      "output": str(args.out)}))


if __name__ == "__main__":
    main()

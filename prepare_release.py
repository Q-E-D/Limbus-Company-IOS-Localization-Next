#!/usr/bin/env python3
"""Offline validation, optional JSON overlay packing, and release staging.

Adapts JSON text to a supplied glyph reference; does not replace game fonts,
prove translations safe, or publish anything.
"""
import argparse
import hashlib
import io
import json
import re
import stat
import tempfile
import zipfile
from collections import Counter, defaultdict, deque
from pathlib import Path, PurePosixPath

MAX_ASSET = 32 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
PREFIX = "Assets/Resources_moved/Localize/"
TEXT_KEYS = set("""
content desc name title teller text dlg summary place simpleDesc flavor
displayName message nickName abName messageDesc description story songWriter
behaveDesc eventDesc prevDesc successDesc failureDesc subDesc nameWithTitle
clue dialog usage statText panicName panicDescription lowMoraleDescription
shortName add min openCondition relatedChapterText company area chapter
chaptertitle sentence teacher mainText subText variation rawDesc
openConditionNumber variation2 parttitle askLevelUp longName abnormalityName
specialName skinItemTitle skinItemDesc speaker nameList result
""".split()) | {f"goalDescription{i}" for i in range(1, 9)}
IDENTITY_KEYS = ("id", "key", "index", "level", "abilityID", "d")
# These schemas use ordered entries rather than IDs. A length mismatch is
# reported and left in Japanese instead of shifting entries into other slots.
POSITIONAL_LIST_KEYS = {"options", "coinlist", "coindescs", "texts"}
PATCH_SUFFIX = re.compile(r"-a1c\d+p\d+(?=\.json$)")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"Nonstandard JSON constant: {value}")


def parse_json(data):
    return json.loads(data.decode("utf-8-sig"), object_pairs_hook=pairs,
                      parse_constant=reject_constant)


def load_charset(path):
    """Load a conservative coverage reference, not the actual game font."""
    chars = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            chars.update(line)
    require(chars, f"Empty font charset: {path}")
    return chars


def load_glyph_map(path, charset):
    mapping = parse_json(path.read_bytes())
    require(isinstance(mapping, dict), "Glyph map must be an object")
    result = {}
    for source, target in mapping.items():
        require(isinstance(source, str) and len(source) == 1
                and isinstance(target, str) and len(target) == 1,
                "Glyph map entries must map one character to one character")
        require(target in charset, f"Glyph map target is outside charset: {target}")
        if source not in charset:
            result[ord(source)] = target
    return result


def _text_key(key):
    return key in TEXT_KEYS


def adapt_text(value, key, charset, glyph_map, report):
    """Adapt only visible text leaves; keys, IDs and asset paths stay untouched."""
    if isinstance(value, str) and _text_key(key):
        translated = value.translate(glyph_map)
        missing = sorted({c for c in translated if c not in charset and _is_cjk(c)})
        for char in missing:
            report["missing_chars"][char] += 1
        for source, target in zip(value, translated):
            if source != target:
                report["mapped_chars"][f"{source}->{target}"] += 1
        return translated
    if isinstance(value, list):
        return [adapt_text(item, key, charset, glyph_map, report) for item in value]
    if isinstance(value, dict):
        return {name: adapt_text(item, name, charset, glyph_map, report)
                for name, item in value.items()}
    return value


def _is_cjk(char):
    code = ord(char)
    return (0x3400 <= code <= 0x4DBF or 0x4E00 <= code <= 0x9FFF
            or 0xF900 <= code <= 0xFAFF or 0x20000 <= code <= 0x323AF)


def _identity(row):
    if isinstance(row, dict):
        for key in IDENTITY_KEYS:
            value = row.get(key)
            if type(value) in (str, int):
                model = row.get("model") if isinstance(row.get("model"), str) else None
                return key, type(value).__name__, value, model
    return None


def _merge_value(target, source, key, report, path=""):
    if isinstance(target, str) and isinstance(source, str):
        if not _text_key(key):
            return target
        report["field_replacements"][key] += 1
        return source
    if isinstance(target, dict) and isinstance(source, dict):
        # A different model is a different speaker/scene, even with the same ID.
        if "model" in target and "model" in source and target["model"] != source["model"]:
            report["unmerged_paths"].append(path + ": model mismatch")
            return target
        result = {name: _merge_value(item, source[name], name, report,
                                    f"{path}/{name}")
                  if name in source else item for name, item in target.items()}
        if "model" in target and "content" in target:
            for name in ("teller", "title"):
                if name not in target and isinstance(source.get(name), str):
                    result[name] = source[name]
                    report["field_replacements"][name] += 1
        return result
    if isinstance(target, list) and isinstance(source, list):
        source_by_id = defaultdict(deque)
        for item in source:
            identity = _identity(item)
            if identity is not None:
                source_by_id[identity].append(item)
        target_counts = Counter(_identity(item) for item in target)
        has_ids = any(identity is not None for identity in target_counts)
        ambiguous = {identity for identity, count in target_counts.items()
                     if identity is not None and max(count, len(source_by_id[identity])) > 1
                     and count != len(source_by_id[identity])}
        if not has_ids and target:
            # Only known ordered schemas, or visible string arrays, can use position.
            ordered = (key in POSITIONAL_LIST_KEYS or
                       (_text_key(key) and all(isinstance(v, str) for v in target + source)))
            if not ordered or len(target) != len(source):
                report["unmerged_paths"].append(path + ": no stable identity or length mismatch")
                return target
        result = []
        for index, item in enumerate(target):
            replacement = None
            identity = _identity(item)
            if identity is not None and identity not in ambiguous and source_by_id[identity]:
                replacement = source_by_id[identity].popleft()
                if key == "dataList":
                    report["matched_rows"] += 1
            elif not has_ids and index < len(source):
                replacement = source[index]
            elif has_ids:
                report["unmerged_paths"].append(f"{path}/{index}: unmatched or ambiguous identity")
            result.append(_merge_value(item, replacement, key, report, f"{path}/{index}")
                          if replacement is not None else item)
        return result
    return target


def build_overlay_from_llc(jp_zip_data, llc_zip_data, output_dir, charset_path,
                           glyph_map_path=None, glyph_mode="preserve"):
    """Create JP-slot JSON overlays from an LLC Chinese resource archive."""
    charset = load_charset(charset_path)
    require(glyph_mode in {"preserve", "compatible"}, "Unknown glyph mode")
    glyph_map = load_glyph_map(glyph_map_path, charset) if glyph_map_path else {}
    report = {"matched_files": 0, "unmatched_jp_files": [],
              "unused_llc_files": [], "matched_rows": 0,
              "field_replacements": Counter(), "missing_chars": Counter(),
              "mapped_chars": Counter(), "unmerged_paths": [],
              "backfilled_files": [], "speaker_fields_added": Counter(),
              "unknown_story_models": Counter(), "glyph_mode": glyph_mode,
              "missing_glyph_examples": {}}
    with zipfile.ZipFile(io.BytesIO(jp_zip_data)) as jp, \
            zipfile.ZipFile(io.BytesIO(llc_zip_data)) as llc:
        jp_files = _slot_files(jp, jp=True)
        llc_files = _slot_files(llc, jp=False)
        overlays = {}
        for name, jp_name in sorted(jp_files.items()):
            source_name = name if name in llc_files else PATCH_SUFFIX.sub("", name)
            if source_name not in llc_files:
                report["unmatched_jp_files"].append(name)
                continue
            target = parse_json(jp.read(jp_name))
            source = parse_json(llc.read(llc_files[source_name]))
            if not isinstance(target, dict) or not isinstance(source, dict):
                raise ValueError(f"Expected localization JSON objects: {name}")
            before = report["field_replacements"].total()
            merged = _merge_value(target, source, "dataList", report, jp_name)
            if report["field_replacements"].total() > before:
                report["matched_files"] += 1
                overlays[jp_name] = merged
                if source_name != name:
                    report["backfilled_files"].append(name)
        scenario = overlays.get(jp_files.get("ScenarioModelCodes-AutoCreated.json"), {})
        names = {row["id"]: (row.get("name", ""), row.get("nickName", ""))
                 for row in scenario.get("dataList", [])
                 if isinstance(row, dict) and isinstance(row.get("id"), str)}
        for jp_name, merged in sorted(overlays.items()):
            if jp_name.startswith("LocalizeTemp_jp/StoryData/"):
                _fill_speakers(merged, names, report)
            local_report = {"mapped_chars": Counter(), "missing_chars": Counter()}
            merged = adapt_text(merged, "dataList", charset,
                                glyph_map if glyph_mode == "compatible" else {}, local_report)
            for char in local_report["missing_chars"]:
                report["missing_glyph_examples"].setdefault(char, jp_name)
            report["mapped_chars"].update(local_report["mapped_chars"])
            report["missing_chars"].update(local_report["missing_chars"])
            relative = jp_name.removeprefix("LocalizeTemp_jp/")
            destination = output_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((json.dumps(merged, ensure_ascii=False,
                                                separators=(",", ":")) + "\n").encode())
        report["unused_llc_files"] = sorted(set(llc_files) - set(jp_files))
    for field, value in report.items():
        if isinstance(value, Counter):
            report[field] = dict(value)
    report["charset_size"] = len(charset)
    report["glyph_map_size"] = len(glyph_map)
    return report


def _fill_speakers(value, names, report):
    if isinstance(value, dict):
        model = value.get("model")
        if isinstance(model, str) and model and "content" in value:
            if model in names:
                for field, text in zip(("teller", "title"), names[model]):
                    if field not in value:
                        value[field] = text
                        report["speaker_fields_added"][field] += 1
            elif "teller" not in value or "title" not in value:
                report["unknown_story_models"][model] += 1
        for child in value.values():
            _fill_speakers(child, names, report)
    elif isinstance(value, list):
        for child in value:
            _fill_speakers(child, names, report)


def _checked_members(archive, allow_dirs=False):
    infos = archive.infolist()
    require(0 < len(infos) <= 20000, "Unexpected archive entry count")
    require(sum(info.file_size for info in infos) <= MAX_EXPANDED,
            "Archive expands beyond limit")
    seen = set()
    for info in infos:
        name = info.filename.rstrip("/") if info.is_dir() else info.filename
        safe_path(name, json_only=False)
        require(name not in seen, f"Duplicate ZIP entry: {name}")
        seen.add(name)
        require(not info.flag_bits & 1, "Encrypted ZIP entry")
        mode = stat.S_IFMT(info.external_attr >> 16)
        if info.is_dir():
            require(allow_dirs and mode in (0, stat.S_IFDIR), "Unexpected ZIP directory")
        else:
            require(mode in (0, stat.S_IFREG), "Non-regular ZIP entry")
            require(info.file_size <= MAX_ASSET, f"ZIP member too large: {name}")
            yield info


def _slot_files(archive, jp):
    result = {}
    for info in _checked_members(archive, allow_dirs=not jp):
        if not info.filename.endswith(".json"):
            require(not jp, f"Not JSON: {info.filename}")
            continue
        name = PurePosixPath(info.filename).name
        if jp:
            require(info.filename.startswith("LocalizeTemp_jp/") and name.startswith("JP_"),
                    f"Unexpected JP slot: {info.filename}")
            name = name[3:]
        require(name not in result, f"Duplicate resource basename: {name}")
        result[name] = info.filename
    return result


def game_hash(data):
    # Verified against all 2,412 JP entries of ghcruise v1.116.2-alpha.
    return hashlib.md5(data.replace(b"\r\n", b"\n")).hexdigest()


def safe_path(name, json_only=True):
    require(isinstance(name, str), "Path must be a string")
    require(name and not name.startswith("/") and "\\" not in name,
            f"Invalid path: {name!r}")
    require(all(part not in ("", ".", "..") for part in name.split("/")),
            f"Invalid path component: {name!r}")
    require(not any(ord(c) < 32 for c in name), "Control character in path")
    require(not json_only or PurePosixPath(name).suffix == ".json", f"Not JSON: {name}")


def read_asset(path, expected):
    require(re.fullmatch(r"[0-9a-fA-F]{64}", expected) is not None,
            "Expected a SHA-256 digest")
    require(path.stat().st_size <= MAX_ASSET, f"Asset too large: {path}")
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected.lower(),
            f"SHA-256 mismatch: {path}")
    return data


def refresh_jp_hashes(zip_data, manifest_data):
    """Rebuild JP hashes only when ZIP paths and declared sizes already agree."""
    manifest = parse_json(manifest_data)
    require(isinstance(manifest, dict)
            and set(manifest) == {"Version", "EncryptKey", "EncryptIV", "Files",
                                 "SteamUpdateFiles"},
            "Unknown manifest schema")
    files = manifest["Files"]
    require(isinstance(files, dict) and files, "Empty/invalid file map")
    expected_jp = {name for name in files if name.startswith(PREFIX + "jp/")}
    require(expected_jp, "Manifest has no JP files")
    seen = set()
    changed = []
    with zipfile.ZipFile(io.BytesIO(zip_data)) as archive:
        for info in _checked_members(archive):
            safe_path(info.filename)
            require(info.filename.startswith("LocalizeTemp_jp/"),
                    f"Unexpected archive root: {info.filename}")
            mapped = PREFIX + "jp/" + info.filename[len("LocalizeTemp_jp/"):]
            require(mapped not in seen, f"Duplicate ZIP entry: {mapped}")
            seen.add(mapped)
            require(mapped in files, f"Missing manifest entry: {mapped}")
            entry = files[mapped]
            require(isinstance(entry, dict) and set(entry) == {"Hash", "Size", "Crc"},
                    f"Unexpected entry: {mapped}")
            require(type(entry["Size"]) is int and info.file_size == entry["Size"],
                    f"ZIP/manifest size mismatch: {mapped}")
            require(type(entry["Crc"]) is int and entry["Crc"] == 0,
                    f"Unexpected CRC: {mapped}")
            data = archive.read(info)
            require(isinstance(parse_json(data), dict),
                    f"Expected JSON object: {mapped}")
            digest = game_hash(data)
            if digest != entry["Hash"]:
                changed.append(mapped)
                entry["Hash"] = digest
        require(seen == expected_jp, "ZIP/manifest JP file set mismatch")
    refreshed = (json.dumps(manifest, ensure_ascii=False, indent=4) + "\n").encode()
    return refreshed, changed


def validate(zip_data, manifest_data):
    manifest = parse_json(manifest_data)
    require(isinstance(manifest, dict), "Manifest must be an object")
    require(set(manifest) == {"Version", "EncryptKey", "EncryptIV", "Files",
                              "SteamUpdateFiles"}, "Unknown manifest schema")
    require(all(isinstance(manifest[k], str)
                for k in ("Version", "EncryptKey", "EncryptIV")),
            "Invalid manifest metadata")
    require(manifest["SteamUpdateFiles"] is None,
            "Unexpected SteamUpdateFiles; manual review required")
    files = manifest["Files"]
    require(isinstance(files, dict) and files, "Empty/invalid file map")
    for name, entry in files.items():
        safe_path(name)
        require(name.startswith(PREFIX), f"Non-localization path: {name}")
        require(isinstance(entry, dict) and set(entry) == {"Hash", "Size", "Crc"},
                f"Unexpected entry: {name}")
        require(isinstance(entry["Hash"], str)
                and re.fullmatch(r"[0-9a-fA-F]{1,32}", entry["Hash"]) is not None,
                f"Unexpected game hash format: {name}")
        require(type(entry["Size"]) is int and 0 <= entry["Size"] <= MAX_EXPANDED,
                f"Invalid size: {name}")
        require(type(entry["Crc"]) is int and entry["Crc"] == 0,
                f"Unexpected CRC: {name}")
    expected_jp = {name for name in files if name.startswith(PREFIX + "jp/")}
    seen = set()
    with zipfile.ZipFile(io.BytesIO(zip_data)) as archive:
        infos = archive.infolist()
        require(0 < len(infos) <= 20000, "Unexpected archive entry count")
        total = sum(info.file_size for info in infos)
        require(total <= MAX_EXPANDED, "Archive expands beyond limit")
        for info in infos:
            safe_path(info.filename)
            require(info.filename.startswith("LocalizeTemp_jp/"),
                    f"Unexpected archive root: {info.filename}")
            require(not info.flag_bits & 1, "Encrypted ZIP entry")
            mode = info.external_attr >> 16
            require(stat.S_IFMT(mode) in (0, stat.S_IFREG), "Non-regular ZIP entry")
            mapped = PREFIX + "jp/" + info.filename[len("LocalizeTemp_jp/"):]
            require(mapped not in seen, f"Duplicate ZIP entry: {mapped}")
            seen.add(mapped)
            require(mapped in files, f"Missing manifest entry: {mapped}")
            require(info.file_size == files[mapped]["Size"],
                    f"ZIP/manifest size mismatch: {mapped}")
            data = archive.read(info)
            require(game_hash(data) == files[mapped]["Hash"],
                    f"Game hash mismatch: {mapped}")
            require(isinstance(parse_json(data), dict),
                    f"Expected JSON object: {mapped}")
    require(seen == expected_jp, "ZIP/manifest JP file set mismatch")
    return {"zip_json_count": len(seen), "manifest_json_count": len(files),
            "uncompressed_bytes": total,
            "checks": "SHA-256 identity, JSON structure, paths, sizes, LF-MD5, JP file set",
            "limits": "Structure only; no semantic guarantee, actual font replacement, or iOS test"}


def repack(zip_data, manifest_data, overlay):
    """Apply already font-adapted JSONs named like JP_*.json, preserving slots."""
    require(overlay.is_dir() and not overlay.is_symlink(), "Expected overlay directory")
    with zipfile.ZipFile(io.BytesIO(zip_data)) as archive:
        resources = {i.filename: archive.read(i) for i in archive.infolist()}
    changed = 0
    for path in sorted(overlay.rglob("*")):
        require(not path.is_symlink(), f"Overlay symlink: {path}")
        if path.is_dir():
            continue
        relative = path.relative_to(overlay).as_posix()
        safe_path(relative)
        target = "LocalizeTemp_jp/" + relative
        require(target in resources, f"No matching JP slot: {relative}")
        require(path.stat().st_size <= MAX_ASSET, f"Overlay too large: {relative}")
        data = path.read_bytes()
        require(isinstance(parse_json(data), dict), f"Expected object: {relative}")
        resources[target] = data
        changed += 1
    require(changed > 0, "Empty overlay")
    require(sum(map(len, resources.values())) <= MAX_EXPANDED,
            "Result expands beyond limit")
    manifest = parse_json(manifest_data)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(resources.items()):
            entry = manifest["Files"][PREFIX + "jp/" + name[len("LocalizeTemp_jp/"):]]
            entry.update(Hash=game_hash(data), Size=len(data))
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    return buffer.getvalue(), (json.dumps(manifest, ensure_ascii=False, indent=4)
                              + "\n").encode("utf-8"), changed


def make_module(repo, tag):
    require(re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", repo)
            is not None, "Expected GitHub owner/repository")
    require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", tag) is not None
            and tag.lower() != "latest", "Expected a fixed release tag")
    base = f"https://github.com/{repo}/releases/download/{tag}"
    return (
        "#!name=Limbus localization - reviewed release\n"
        f"#!desc=Fixed release {repo}@{tag}; staged offline\n\n"
        "[URL Rewrite]\n"
        r"^https://[^/]+\.limbuscompanycdn\.org/[^?]*localize_jp\.zip(?:\?.*)?$ "
        + base + "/localize_jp.zip 302\n"
        r"^https://downloadcommon\.limbuscompanycdn\.org/[^?]*LocalizePatchInfo\.json(?:\?.*)?$ "
        + base + "/manifest.json 302\n\n"
        "[MITM]\nhostname = %APPEND% *.limbuscompanycdn.org\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--zip-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--repo", required=True, help="Your GitHub owner/repository")
    parser.add_argument("--tag", required=True, help="Your fixed release tag")
    parser.add_argument("--overlay-jp", type=Path,
                        help="Optional prebuilt JP JSON overlay directory")
    parser.add_argument("--llc-zip", type=Path,
                        help="LLC zh-CN ZIP; build a JP overlay from matching IDs")
    parser.add_argument("--llc-zip-sha256",
                        help="Required SHA-256 for --llc-zip")
    parser.add_argument("--font-charset", type=Path,
                        help="Reviewed mobile glyph charset used with --llc-zip")
    parser.add_argument("--glyph-map", type=Path,
                        help="Missing-glyph map required for compatible mode; may alter meaning")
    parser.add_argument("--glyph-mode", choices=("preserve", "compatible"), default="preserve",
                        help="Preserve LLC text (default) or explicitly apply glyph substitutions")
    parser.add_argument("--allow-missing-glyphs", action="store_true",
                        help="Stage an experimental package even when reference coverage is incomplete")
    parser.add_argument("--refresh-jp-hashes", action="store_true",
                        help="Recompute JP Hash fields only when paths and sizes match")
    parser.add_argument("--out", required=True, type=Path, help="New staging directory")
    args = parser.parse_args()
    require(not (args.overlay_jp and args.llc_zip),
            "Choose --overlay-jp or --llc-zip, not both")
    if args.llc_zip:
        require(args.llc_zip_sha256 and args.font_charset,
                "--llc-zip requires --llc-zip-sha256 and --font-charset")
        require(args.glyph_mode != "compatible" or args.glyph_map,
                "Compatible mode requires --glyph-map")
    module = make_module(args.repo, args.tag)
    zip_data = read_asset(args.zip, args.zip_sha256)
    manifest_data = read_asset(args.manifest, args.manifest_sha256)
    inputs = {"localize_jp.zip": hashlib.sha256(zip_data).hexdigest(),
              "manifest.json": hashlib.sha256(manifest_data).hexdigest()}
    refreshed_hashes = []
    if args.refresh_jp_hashes:
        manifest_data, refreshed_hashes = refresh_jp_hashes(zip_data, manifest_data)
    report = validate(zip_data, manifest_data)
    normalized_manifest_sha256 = hashlib.sha256(manifest_data).hexdigest()
    if args.overlay_jp or args.llc_zip:
        overlay_report = None
        with tempfile.TemporaryDirectory(prefix="limbus-overlay-") as directory:
            overlay_dir = Path(directory)
            if args.llc_zip:
                llc_data = read_asset(args.llc_zip, args.llc_zip_sha256)
                inputs["llc.zip"] = hashlib.sha256(llc_data).hexdigest()
                inputs["font_charset"] = hashlib.sha256(args.font_charset.read_bytes()).hexdigest()
                if args.glyph_map:
                    inputs["glyph_map"] = hashlib.sha256(args.glyph_map.read_bytes()).hexdigest()
                overlay_report = build_overlay_from_llc(
                    zip_data, llc_data, overlay_dir, args.font_charset, args.glyph_map, args.glyph_mode)
                if overlay_report["missing_chars"] and not args.allow_missing_glyphs:
                    raise ValueError("Uncovered output glyphs: "
                                     + "".join(sorted(overlay_report["missing_chars"]))
                                     + "; use --allow-missing-glyphs only for local testing")
            else:
                overlay_dir = args.overlay_jp
            zip_data, manifest_data, changed = repack(zip_data, manifest_data, overlay_dir)
        report = validate(zip_data, manifest_data)
        report["overlaid_json_count"] = changed
        if overlay_report is not None:
            report["llc_build"] = overlay_report
            report["experimental"] = True
            report["font_coverage"] = "reference-only; device not verified"
            if args.glyph_mode == "compatible":
                report["text_warning"] = "Glyph substitutions include non-equivalent characters; output is not pure simplified Chinese"
    if args.refresh_jp_hashes:
        report["refreshed_jp_hashes"] = refreshed_hashes
        report["normalized_manifest_sha256"] = normalized_manifest_sha256
    report["input_sha256"] = inputs
    report["sha256"] = {"localize_jp.zip": hashlib.sha256(zip_data).hexdigest(),
                         "manifest.json": hashlib.sha256(manifest_data).hexdigest()}
    report["target"] = f"{args.repo}@{args.tag}"
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "localize_jp.zip").write_bytes(zip_data)
    (args.out / "manifest.json").write_bytes(manifest_data)
    (args.out / "LimbusReviewed.module").write_text(module, encoding="utf-8")
    (args.out / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

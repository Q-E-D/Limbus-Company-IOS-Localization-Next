#!/usr/bin/env python3
"""Offline validation, optional JSON overlay packing, and release staging.

Does not adapt fonts, prove translations safe, or publish anything.
"""
import argparse
import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

MAX_ASSET = 32 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
PREFIX = "Assets/Resources_moved/Localize/"


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


def game_hash(data):
    # Verified against all 2,412 JP entries of ghcruise v1.116.2-alpha.
    return hashlib.md5(data.replace(b"\r\n", b"\n")).hexdigest()


def safe_path(name):
    require(isinstance(name, str), "Path must be a string")
    require(name and not name.startswith("/") and "\\" not in name,
            f"Invalid path: {name!r}")
    require(all(part not in ("", ".", "..") for part in name.split("/")),
            f"Invalid path component: {name!r}")
    require(not any(ord(c) < 32 for c in name), "Control character in path")
    require(PurePosixPath(name).suffix == ".json", f"Not JSON: {name}")


def read_asset(path, expected):
    require(re.fullmatch(r"[0-9a-fA-F]{64}", expected) is not None,
            "Expected a SHA-256 digest")
    require(path.stat().st_size <= MAX_ASSET, f"Asset too large: {path}")
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected.lower(),
            f"SHA-256 mismatch: {path}")
    return data


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
            "limits": "No semantic security guarantee, font adaptation, or iOS test"}


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
                        help="Optional font-adapted JP JSON directory; no new slots")
    parser.add_argument("--out", required=True, type=Path, help="New staging directory")
    args = parser.parse_args()
    module = make_module(args.repo, args.tag)
    zip_data = read_asset(args.zip, args.zip_sha256)
    manifest_data = read_asset(args.manifest, args.manifest_sha256)
    report = validate(zip_data, manifest_data)
    inputs = {"localize_jp.zip": hashlib.sha256(zip_data).hexdigest(),
              "manifest.json": hashlib.sha256(manifest_data).hexdigest()}
    if args.overlay_jp:
        zip_data, manifest_data, changed = repack(zip_data, manifest_data, args.overlay_jp)
        report = validate(zip_data, manifest_data)
        report["overlaid_json_count"] = changed
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

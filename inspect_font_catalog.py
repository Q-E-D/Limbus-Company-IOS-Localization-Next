#!/usr/bin/env python3
"""Read font locations and dependencies from a Unity Addressables v2 catalog.

Read-only subset of the layout documented by Addressables 2.7.6:
ContentCatalogData.ResourceLocator and BinaryStorageBuffer (see docs/FONT-INVESTIGATION.md).
This does not resolve RuntimePath, load bundles, or modify the catalog.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from prepare_release import MAX_ASSET, require

NULL = 0xFFFFFFFF
MASK = 0x3FFFFFFF


class Catalog:
    def __init__(self, data):
        require(32 <= len(data) <= MAX_ASSET, "Invalid catalog size")
        self.data = data
        header = self.values(0, 8)
        require(header[0] == 0x0DE38942 and header[1] == 2,
                "Expected Unity Addressables binary catalog version 2")
        self.keys_offset = header[2]

    def values(self, offset, count):
        require(0 <= offset <= len(self.data) and 0 <= count <= len(self.data) // 4
                and count * 4 <= len(self.data) - offset, "Catalog offset out of bounds")
        return struct.unpack_from("<" + "I" * count, self.data, offset)

    def array(self, offset):
        if offset == NULL:
            return ()
        require(offset >= 4, "Invalid catalog array offset")
        length, = self.values(offset - 4, 1)
        require(length % 4 == 0, "Invalid catalog array byte length")
        return self.values(offset, length // 4)

    def string(self, offset, separator="/"):
        if offset == NULL:
            return None
        if offset & 0x40000000:
            parts, seen = [], set()
            while offset != NULL:
                offset &= MASK
                require(offset not in seen and len(seen) < 1024,
                        "Cyclic or excessive catalog string chain")
                seen.add(offset)
                part, offset = self.values(offset, 2)
                require(not part & 0x40000000, "Nested catalog string chain")
                parts.append(self.string(part))
            require(all(part is not None for part in parts), "Null catalog string segment")
            return separator.join(reversed(parts))
        position = offset & MASK
        require(position >= 4, "Invalid catalog string offset")
        length, = self.values(position - 4, 1)
        require(length <= len(self.data) - position, "Catalog string out of bounds")
        encoding = "utf-16-le" if offset & 0x80000000 else "ascii"
        return self.data[position:position + length].decode(encoding)

    def location(self, offset):
        key, internal, provider, dependencies, _, _, _ = self.values(offset, 7)
        return {"offset": offset, "primary_key": self.string(key),
                "internal_id": self.string(internal),
                "provider": self.string(provider, "."),
                "dependency_offsets": list(self.array(dependencies))}

    def locations(self):
        keys = self.array(self.keys_offset)
        require(len(keys) % 2 == 0, "Invalid catalog key table")
        offsets = set()
        for location_set in keys[1::2]:
            offsets.update(self.array(location_set))
        return {offset: self.location(offset) for offset in sorted(offsets)}


def inspect_fonts(data):
    locations = Catalog(data).locations()
    fonts = []
    for location in locations.values():
        label = (location["primary_key"] or "") + " " + (location["internal_id"] or "")
        if "font" not in label.lower():
            continue
        entry = dict(location)
        dependencies = []
        for offset in location["dependency_offsets"]:
            require(offset in locations, "Unknown catalog dependency")
            dependencies.append(locations[offset])
        entry["dependencies"] = dependencies
        fonts.append(entry)
    return {"catalog_sha256": hashlib.sha256(data).hexdigest(),
            "catalog_version": 2, "location_count": len(locations),
            "font_locations": fonts,
            "limits": "Directory evidence only; no bundle contents, font coverage, or device validation"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    args = parser.parse_args()
    require(args.catalog.stat().st_size <= MAX_ASSET, "Catalog too large")
    print(json.dumps(inspect_fonts(args.catalog.read_bytes()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

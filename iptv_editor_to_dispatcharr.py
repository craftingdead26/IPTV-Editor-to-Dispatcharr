#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


ATTRIBUTE_PATTERN = re.compile(r'([A-Za-z0-9_-]+)="([^"]*)"')
PREFERRED_ATTRIBUTE_ORDER = ("tvg-id", "tvg-name", "tvg-logo", "group-title")


@dataclass
class Channel:
    name: str
    url: str
    attrs: dict[str, str]


def parse_extinf(line: str) -> tuple[dict[str, str], str]:
    payload = line[len("#EXTINF:") :].strip()
    attrs_part, _, name = payload.partition(",")
    attrs = {key: value for key, value in ATTRIBUTE_PATTERN.findall(attrs_part) if value}
    return attrs, name.strip()


def parse_m3u(path: Path) -> list[Channel]:
    channels: list[Channel] = []
    pending_attrs: dict[str, str] | None = None
    pending_name = ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            pending_attrs, pending_name = parse_extinf(line)
            continue
        if line.startswith("#"):
            continue
        if pending_attrs is None:
            continue
        name = pending_name or pending_attrs.get("tvg-name", "Unknown")
        channels.append(Channel(name=name, url=line, attrs=pending_attrs))
        pending_attrs = None
        pending_name = ""

    return channels


def sort_attrs(attrs: dict[str, str]) -> list[tuple[str, str]]:
    ordered: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key in PREFERRED_ATTRIBUTE_ORDER:
        value = attrs.get(key, "").strip()
        if value:
            ordered.append((key, value))
            seen.add(key)

    for key in sorted(attrs):
        if key in seen:
            continue
        value = attrs[key].strip()
        if value:
            ordered.append((key, value))

    return ordered


def to_m3u(channels: list[Channel]) -> str:
    lines = ["#EXTM3U"]
    for channel in channels:
        attrs = dict(channel.attrs)
        if channel.name and not attrs.get("tvg-name"):
            attrs["tvg-name"] = channel.name
        sorted_attrs = sort_attrs(attrs)
        attr_text = " ".join(f'{key}="{value}"' for key, value in sorted_attrs)
        lines.append(f"#EXTINF:-1 {attr_text},{channel.name}".rstrip())
        lines.append(channel.url)
    return "\n".join(lines) + "\n"


def to_dispatcharr_json(channels: list[Channel]) -> str:
    payload = {
        "channels": [
            {
                "name": channel.name,
                "stream_url": channel.url,
                "epg_channel_id": channel.attrs.get("tvg-id", ""),
                "logo": channel.attrs.get("tvg-logo", ""),
                "group": channel.attrs.get("group-title", ""),
            }
            for channel in channels
        ]
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert an IPTV Editor M3U export to Dispatcharr-friendly output.")
    parser.add_argument("input_file", type=Path, help="Path to IPTV Editor M3U playlist.")
    parser.add_argument("-o", "--output", type=Path, help="Output file path. If omitted, prints to stdout.")
    parser.add_argument(
        "--format",
        choices=("m3u", "json"),
        default="m3u",
        help="Output format: normalized M3U or Dispatcharr JSON payload.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    channels = parse_m3u(args.input_file)
    if not channels:
        parser.error("No channels were found in the provided playlist.")

    output = to_m3u(channels) if args.format == "m3u" else to_dispatcharr_json(channels)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

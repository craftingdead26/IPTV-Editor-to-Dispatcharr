# IPTV-Editor-to-Dispatcharr
an IPTV Editor to Dispatcharr script

## Usage

Convert an IPTV Editor exported `.m3u` playlist into a Dispatcharr-friendly output.

```bash
python3 iptv_editor_to_dispatcharr.py input.m3u -o dispatcharr.m3u
```

Generate Dispatcharr JSON payload instead of M3U:

```bash
python3 iptv_editor_to_dispatcharr.py input.m3u --format json -o dispatcharr.json
```

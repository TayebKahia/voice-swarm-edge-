#!/usr/bin/env python3
"""Fetch the noise corpora and Piper voices the round-trip pipeline needs.

The bytes are large and licensed elsewhere, so they are **not** committed
(`.gitignore` excludes `data/noise/*`). This script plus `data/asset_manifest.json`
are the record of where they came from: every file carries its source URL, its
SHA-256 as retrieved, and the licence under which it is used. The corpus table in
`dataset_card.md` §6 is rewritten from that manifest on every run, between the
`<!-- corpora:begin -->` markers, so the card cannot drift from the bytes.

Two noise sources, in the order of preference `02_dataset_plan.md` §5 sets out:

  DREGON   UAV-embedded rotor noise recorded on a flying quadrotor --- the *right*
           citation for propeller noise, and directly downloadable. We take the
           `hovering_nosource_room2` flight, which is ego-noise with no source
           playing, so the file is pure propeller wash.
  ESC-50   `helicopter` and `engine` classes, as environmental backing. ESC-50 is
           CC-BY-NC, which is fine for a non-commercial thesis and is recorded as
           such rather than glossed.

Usage:
    python data/fetch_assets.py              # noise + voices, skip what is present
    python data/fetch_assets.py --noise      # noise corpora only
    python data/fetch_assets.py --voices     # Piper voices only
    python data/fetch_assets.py --verify     # re-hash what is on disk, download nothing

Idempotent: a file whose SHA-256 already matches the manifest is left alone.
Exits non-zero if any requested asset is missing or fails verification.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent
NOISE_DIR = DATA_DIR / "noise"
VOICES_DIR = DATA_DIR / "tts_voices"
MANIFEST_PATH = DATA_DIR / "asset_manifest.json"
CARD_PATH = DATA_DIR / "dataset_card.md"
CARD_BEGIN = "<!-- corpora:begin -->"
CARD_END = "<!-- corpora:end -->"

ESC50_META_URL = "https://raw.githubusercontent.com/karoldvl/ESC-50/master/meta/esc50.csv"
ESC50_AUDIO_BASE = "https://raw.githubusercontent.com/karoldvl/ESC-50/master/audio"
ESC50_CLASSES = ("helicopter", "engine")
ESC50_HOMEPAGE = "https://github.com/karoldvl/ESC-50"
ESC50_LICENCE = "CC BY-NC 3.0 (non-commercial; this is a non-commercial thesis)"

DREGON_URL = "http://dregon.inria.fr/?smd_process_download=1&download_id=356"
DREGON_FILENAME = "DREGON_hovering_nosource_room2.wav"
DREGON_HOMEPAGE = "https://dregon.inria.fr/"
DREGON_LICENCE = (
    "Free to use for academic and educational purpose (dregon.inria.fr, "
    "verbatim from the dataset homepage). Cite Strauss et al., IROS 2018."
)

PIPER_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
PIPER_LICENCE = "MIT (piper-voices repository); underlying corpora per voice MODEL_CARD"
PIPER_HOMEPAGE = "https://huggingface.co/rhasspy/piper-voices"

# Three voices, not one. A single TTS voice gives whisper.cpp one narrow error
# signature to make, and the model would learn that signature rather than the
# shape of ASR error in general.
PIPER_VOICES: tuple[tuple[str, str], ...] = (
    ("en_US-lessac-medium", "en/en_US/lessac/medium"),
    ("en_US-ryan-medium", "en/en_US/ryan/medium"),
    ("en_GB-alba-medium", "en/en_GB/alba/medium"),
)

USER_AGENT = "pfe-swarm-dataset/1.0 (academic use)"
CHUNK = 1 << 16


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, dest: Path) -> None:
    """Fetch `url` to `dest` atomically, so an interrupted run leaves no half-file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response, open(tmp, "wb") as out:
        while block := response.read(CHUNK):
            out.write(block)
    tmp.replace(dest)


def load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.is_file():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"retrieved": None, "assets": {}}


def save_manifest(manifest: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest["retrieved"] = date.today().isoformat()
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def record(
    manifest: dict[str, Any],
    key: str,
    path: Path,
    url: str,
    corpus: str,
    licence: str,
    homepage: str,
    **extra: Any,
) -> None:
    manifest["assets"][key] = {
        "path": str(path.relative_to(DATA_DIR.parent)),
        "url": url,
        "corpus": corpus,
        "licence": licence,
        "homepage": homepage,
        "bytes": path.stat().st_size,
        "sha256": sha256_of(path),
        **extra,
    }


def ensure(
    manifest: dict[str, Any],
    key: str,
    path: Path,
    url: str,
    *,
    corpus: str,
    licence: str,
    homepage: str,
    verify_only: bool,
    **extra: Any,
) -> bool:
    """Return True if `path` is present and matches the manifest after this call."""
    known = manifest["assets"].get(key)
    if path.is_file() and known and known.get("sha256") == sha256_of(path):
        return True
    if verify_only:
        print(f"    [-] {key}: {'hash mismatch' if path.is_file() else 'missing'}")
        return False
    if not path.is_file():
        try:
            download(url, path)
        except (urllib.error.URLError, OSError) as exc:
            print(f"    [-] {key}: download failed ({exc})")
            return False
    record(manifest, key, path, url, corpus, licence, homepage, **extra)
    return True


def fetch_esc50(manifest: dict[str, Any], verify_only: bool) -> bool:
    dest_dir = NOISE_DIR / "esc50"
    meta_path = dest_dir / "esc50.csv"

    if not meta_path.is_file():
        if verify_only:
            print("    [-] esc50.csv missing")
            return False
        try:
            download(ESC50_META_URL, meta_path)
        except (urllib.error.URLError, OSError) as exc:
            print(f"    [-] esc50.csv: download failed ({exc})")
            return False

    with open(meta_path, newline="", encoding="utf-8") as fh:
        wanted = [row for row in csv.DictReader(fh) if row["category"] in ESC50_CLASSES]

    if not wanted:
        print(f"    [-] esc50.csv lists none of {ESC50_CLASSES}")
        return False

    ok = True
    for row in wanted:
        name = row["filename"]
        ok &= ensure(
            manifest,
            f"esc50/{name}",
            dest_dir / name,
            f"{ESC50_AUDIO_BASE}/{name}",
            corpus="ESC-50",
            licence=ESC50_LICENCE,
            homepage=ESC50_HOMEPAGE,
            verify_only=verify_only,
            esc50_category=row["category"],
            esc50_fold=int(row["fold"]),
        )
    print(f"    [+] ESC-50: {len(wanted)} clips across {sorted(set(ESC50_CLASSES))}")
    return ok


def fetch_dregon(manifest: dict[str, Any], verify_only: bool) -> bool:
    path = NOISE_DIR / "dregon" / DREGON_FILENAME
    ok = ensure(
        manifest,
        f"dregon/{DREGON_FILENAME}",
        path,
        DREGON_URL,
        corpus="DREGON",
        licence=DREGON_LICENCE,
        homepage=DREGON_HOMEPAGE,
        verify_only=verify_only,
        note="8-channel 44.1 kHz array recording; channel 0 is used, ego-noise only (no source playing)",
    )
    if ok:
        print(f"    [+] DREGON: {DREGON_FILENAME} ({path.stat().st_size / 1e6:.0f} MB)")
    return ok


def fetch_voices(manifest: dict[str, Any], verify_only: bool) -> bool:
    ok = True
    for voice, remote_dir in PIPER_VOICES:
        for ext in ("onnx", "onnx.json"):
            name = f"{voice}.{ext}"
            ok &= ensure(
                manifest,
                f"piper/{name}",
                VOICES_DIR / name,
                f"{PIPER_BASE}/{remote_dir}/{name}",
                corpus="piper-voices",
                licence=PIPER_LICENCE,
                homepage=PIPER_HOMEPAGE,
                verify_only=verify_only,
            )
    print(f"    [+] Piper voices: {', '.join(v for v, _ in PIPER_VOICES)}")
    return ok


def card_table(manifest: dict[str, Any]) -> str:
    """The §6 corpus table, one row per corpus, rendered from the manifest."""
    grouped: dict[str, dict[str, Any]] = {}
    for entry in manifest["assets"].values():
        corpus = entry.get("corpus", "?")
        summary = grouped.setdefault(
            corpus,
            {"files": 0, "bytes": 0, "licence": entry.get("licence", ""), "url": entry.get("homepage", "")},
        )
        summary["files"] += 1
        summary["bytes"] += int(entry.get("bytes", 0))

    lines = [
        CARD_BEGIN,
        "",
        "| Corpus | Files | Size | Licence | URL |",
        "|---|---:|---:|---|---|",
    ]
    for corpus in sorted(grouped):
        s = grouped[corpus]
        lines.append(
            f"| {corpus} | {s['files']} | {s['bytes'] / 1e6:.1f} MB | {s['licence']} | <{s['url']}> |"
        )
    lines += [
        "",
        f"Retrieved {manifest['retrieved']}. Fetched and verified by "
        f"`python data/fetch_assets.py`; per-file SHA-256 in `data/asset_manifest.json`.",
        "",
        CARD_END,
    ]
    return "\n".join(lines)


def update_card(manifest: dict[str, Any], card_path: Path = CARD_PATH) -> bool:
    """Rewrite the marked block in the dataset card. Returns False if unmarked."""
    if not card_path.is_file():
        return False
    text = card_path.read_text(encoding="utf-8")
    start, end = text.find(CARD_BEGIN), text.find(CARD_END)
    if start < 0 or end < 0:
        return False
    card_path.write_text(
        text[:start] + card_table(manifest) + text[end + len(CARD_END) :], encoding="utf-8"
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch noise corpora and Piper voices.")
    parser.add_argument("--noise", action="store_true", help="noise corpora only")
    parser.add_argument("--voices", action="store_true", help="Piper voices only")
    parser.add_argument(
        "--verify", action="store_true", help="re-hash what is on disk; download nothing"
    )
    args = parser.parse_args()

    want_noise = args.noise or not args.voices
    want_voices = args.voices or not args.noise

    manifest = load_manifest()
    ok = True

    if want_noise:
        print("[*] Noise corpora")
        ok &= fetch_dregon(manifest, args.verify)
        ok &= fetch_esc50(manifest, args.verify)
    if want_voices:
        print("[*] Piper voices")
        ok &= fetch_voices(manifest, args.verify)

    if not args.verify:
        save_manifest(manifest)
        print(f"[*] Manifest written: {MANIFEST_PATH.relative_to(DATA_DIR.parent)}")
        if update_card(manifest):
            print(f"[*] Dataset card §6 rewritten from the manifest")
        else:
            print(f"[!] {CARD_PATH.name} has no {CARD_BEGIN} block; §6 not updated")

    if not ok:
        print("\n[-] One or more assets are missing or failed verification.")
        return 1
    print("\n[+] All requested assets present and verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

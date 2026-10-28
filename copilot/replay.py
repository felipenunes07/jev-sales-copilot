"""Load hand-written call transcripts (JSON or plain text) for replay and evaluation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CALLS_DIR = Path(__file__).resolve().parent.parent / "data" / "calls"

_LINE_RE = re.compile(r"^\s*(?:\[?(\d+(?:\.\d+)?)\]?\s*)?(rep|prospect)\s*:\s*(.+?)\s*$", re.IGNORECASE)


PREFERRED_ORDER = {"good": 0, "bad": 1, "mixed": 2}


# Real client calls cannot live in the (public) repo: in production they are fetched once from private-by-obscurity
# URLs listed in PRIVATE_CALLS_URLS (comma-separated JSON files, e.g. on Vercel Blob) and kept in memory.
_REMOTE: dict[str, dict[str, Any]] = {}


def load_remote_calls(urls: str) -> list[str]:
    """Fetch each call JSON once; returns the ids loaded. A URL that fails is logged and skipped."""
    import logging

    import httpx

    loaded = []
    for url in (u.strip() for u in urls.split(",")):
        if not url:
            continue
        try:
            call = _normalize(httpx.get(url, timeout=20.0, follow_redirects=True).raise_for_status().json(), "remote")
        except Exception as exc:  # noqa: BLE001 - one bad URL must not take the app down
            logging.getLogger("copilot.replay").warning("could not load call from %s: %s", url.split("?")[0], exc)
            continue
        _REMOTE[call["id"]] = call
        loaded.append(call["id"])
    return loaded


def _summary(call: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": call["id"],
        "title": call.get("title", call["id"]),
        "description": call.get("description", ""),
        "expected": call.get("expected", ""),
        "utterances": len(call["utterances"]),
        "duration_s": call["utterances"][-1]["t"] if call["utterances"] else 0,
        "video": call.get("video"),  # {"youtube_id"| "file" | "url": ...} when the call is a real recording
    }


def list_calls(calls_dir: Path = CALLS_DIR) -> list[dict[str, Any]]:
    out = [_summary(load_call(p)) for p in sorted(calls_dir.glob("*.json"), key=lambda p: (PREFERRED_ORDER.get(p.stem, 99), p.stem))]
    local = {c["id"] for c in out}
    return out + [_summary(c) for cid, c in _REMOTE.items() if cid not in local]


def _normalize(call: dict[str, Any], default_id: str) -> dict[str, Any]:
    call.setdefault("id", default_id)
    for i, u in enumerate(call["utterances"]):
        u.setdefault("t", float(i * 8))
        u["speaker"] = u["speaker"].lower()
    return call


def load_call(path_or_id: str | Path, calls_dir: Path = CALLS_DIR) -> dict[str, Any]:
    """Load a call by id (`good`), by JSON path, or by plain-text path (`speaker: text` per line)."""
    path = Path(path_or_id)
    if not path.exists() and str(path_or_id) in _REMOTE and not (calls_dir / f"{path_or_id}.json").exists():
        return json.loads(json.dumps(_REMOTE[str(path_or_id)]))  # a copy: callers may mutate it
    if not path.exists():
        candidate = calls_dir / f"{path_or_id}.json"
        if not candidate.exists():
            raise FileNotFoundError(f"No call '{path_or_id}' (looked in {calls_dir})")
        path = candidate
    if path.suffix.lower() == ".json":
        with open(path, encoding="utf-8") as f:
            return _normalize(json.load(f), path.stem)
    return parse_text_transcript(path.read_text(encoding="utf-8"), call_id=path.stem)


def parse_text_transcript(text: str, call_id: str = "transcript") -> dict[str, Any]:
    """`rep: ...` / `prospect: ...` per line; optional leading `[seconds]`. Missing times are spaced by word count."""
    utterances: list[dict[str, Any]] = []
    t = 0.0
    for line in text.splitlines():
        m = _LINE_RE.match(line)
        if not m:
            continue
        ts, speaker, body = m.groups()
        if ts is not None:
            t = float(ts)
        utterances.append({"t": t, "speaker": speaker.lower(), "text": body})
        t += max(3.0, len(body.split()) / 2.5)
    return {"id": call_id, "title": call_id, "description": "", "expected": "", "utterances": utterances}

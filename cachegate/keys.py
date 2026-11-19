"""Canonical cache keys."""

import hashlib
import json

from .provider import Request

KEY_VERSION = "v1"


def request_key(request: Request) -> str:
    """Hash the fields that decide the answer; ignore metadata and field order."""
    canonical = json.dumps(
        {
            "model": request.model,
            "prompt": request.prompt,
            "temperature": float(request.temperature),
            "max_tokens": int(request.max_tokens),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    # The version prefix lets a future key change invalidate old entries.
    return f"{KEY_VERSION}:{digest}"

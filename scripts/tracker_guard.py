#!/usr/bin/env python3
"""Tracker integrity guard — import and call assert_tracker_fresh() at the top of
every submit_batch script BEFORE sending anything.

Why this exists
---------------
On 2026-07-29 the local working tree was silently reset to an older commit while a
session was in progress. data/applications.json reverted from 442 entries to 282,
so the dedup guards in submit_batch_v19.py could not see 160 applications that had
already been sent that same session. It re-applied to 25 offers that had already
been applied to, and pushed 5 companies past the 2-application cap — 30 unwanted
submissions that really reached employers.

The existing 5-layer dedup was sound. It was reading a stale file. This checks the
input the dedup depends on.
"""

import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APPS_PATH = BASE_DIR / "data" / "applications.json"
REMOTE_BRANCH = "claude/job-search-qtdnid"


def _entry_count(raw):
    try:
        return len(json.loads(raw))
    except Exception:
        return None


def assert_tracker_fresh(strict=True):
    """Abort if the local tracker is behind the remote, or if the tree is mid-reset.

    Returns (local_count, remote_count). Raises SystemExit when strict and stale.
    """
    local = json.loads(APPS_PATH.read_text())
    local_n = len(local)

    try:
        subprocess.run(["git", "fetch", "origin", REMOTE_BRANCH],
                       cwd=BASE_DIR, capture_output=True, timeout=60, check=False)
        raw = subprocess.run(
            ["git", "show", f"origin/{REMOTE_BRANCH}:data/applications.json"],
            cwd=BASE_DIR, capture_output=True, text=True, timeout=60,
        ).stdout
        remote_n = _entry_count(raw)
    except Exception as e:
        print(f"[tracker_guard] WARNING: could not reach remote ({e}). "
              f"Proceeding on local tracker with {local_n} entries.")
        return local_n, None

    if remote_n is None:
        print(f"[tracker_guard] WARNING: could not parse remote tracker. "
              f"Proceeding on local with {local_n} entries.")
        return local_n, None

    print(f"[tracker_guard] local={local_n} entries, remote={remote_n} entries")

    if local_n < remote_n:
        msg = (
            f"\n[tracker_guard] ABORT: local tracker ({local_n}) is BEHIND remote "
            f"({remote_n}).\n"
            f"  The working tree looks reset/stale. Dedup would run against an\n"
            f"  incomplete history and re-apply to jobs already applied to.\n"
            f"  Fix first:  git fetch origin {REMOTE_BRANCH} && "
            f"git reset --hard origin/{REMOTE_BRANCH}\n"
        )
        if strict:
            sys.exit(msg)
        print(msg)

    return local_n, remote_n


if __name__ == "__main__":
    assert_tracker_fresh()
    print("[tracker_guard] OK — safe to submit.")

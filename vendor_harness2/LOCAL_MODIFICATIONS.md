# Local modifications to Harness²

This directory is a vendored copy of [google-research/harness2](https://github.com/google-research/harness2)
at commit `1cfe254e8d25b15f37048c3730134686abe60335` (2026-10-13), licensed under Apache 2.0 (see `LICENSE`).

The upstream code targets Linux. These files were modified so the core runs natively on Windows.
The exact changes are in [`LOCAL_PATCHES.diff`](LOCAL_PATCHES.diff); apply them to a fresh clone with
`git apply LOCAL_PATCHES.diff`.

| File | Change |
|---|---|
| `harness2/core/schedule.py` | `fcntl` (POSIX-only file locking) falls back to `msvcrt` on Windows. |
| `harness2/core/tree.py` | Relative paths use `as_posix()` so harness file keys don't contain backslashes. |
| `harness2/core/runmark.py` | Same `as_posix()` fix when fingerprinting a tree. |
| `harness2/core/proposer.py` | Same `as_posix()` fix in the call fingerprint. |
| `harness2/core/context.py` | Evidence folders are deleted with a handler that clears read-only flags and retries. Windows (and OneDrive) can mark folders read-only, which `shutil.rmtree` cannot remove. |

No other upstream files were changed. The surrounding project (`slide_agent/`, `h2/`) is separate code that uses this package.

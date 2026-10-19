
import inspect
import time
from pathlib import Path
import sys

print("Starting query audit...", flush=True)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import analytics.queries as queries

DEFAULTS = {
    "state": "Maharashtra",
    "commodity": "Onion",
    "market": None,
    "market1": None,
    "market2": None,
    "start_date": "2026-01-01",
    "end_date": "2026-04-21",
    "start": "2026-01-01",
    "end": "2026-04-21",
    "days": 90,
    "limit": 10,
    "top_n": 10,
    "n": 10,
}

results = []

for name, func in inspect.getmembers(queries, inspect.isfunction):
    if func.__module__ != queries.__name__:
        continue

    if not name.startswith(("get_", "compare_", "fetch_", "load_")):
        continue

    sig = inspect.signature(func)
    kwargs = {}
    unsupported = []

    for param_name, param in sig.parameters.items():
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        if param.default is not inspect.Parameter.empty:
            continue

        if param_name in DEFAULTS:
            kwargs[param_name] = DEFAULTS[param_name]
        else:
            unsupported.append(param_name)

    print(f"\nTesting: {name}{sig}", flush=True)

    if unsupported:
        print(f"SKIPPED: needs parameters {unsupported}", flush=True)
        continue

    start_time = time.perf_counter()

    try:
        result = func(**kwargs)
        elapsed = time.perf_counter() - start_time

        size = (
            len(result)
            if isinstance(result, (list, tuple, dict, set, str))
            else "N/A"
        )

        print(
            f"SUCCESS | {elapsed:.2f}s | "
            f"type={type(result).__name__} | rows/size={size}",
            flush=True,
        )
        results.append((name, elapsed, "SUCCESS"))

    except Exception as exc:
        elapsed = time.perf_counter() - start_time
        print(
            f"FAILED | {elapsed:.2f}s | "
            f"{type(exc).__name__}: {exc}",
            flush=True,
        )
        results.append((name, elapsed, "FAILED"))

print("\n========== SLOWEST QUERIES ==========", flush=True)

for name, elapsed, status in sorted(
    results, key=lambda item: item[1], reverse=True
):
    print(f"{elapsed:8.2f}s | {status:7} | {name}", flush=True)

print("\nAudit finished.", flush=True)

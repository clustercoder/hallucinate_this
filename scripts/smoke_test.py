#!/usr/bin/env python3
"""Lightweight repo smoke test: checks essential files exist and are non-empty.
Exits 0 on success, non-zero on failure.
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(__file__))
files_to_check = [
    "pyproject.toml",
    "run_dcipher.py",
    "run_single_executor.py",
    "run_baseline.py",
    "setup_dcipher.sh",
    "setup_baseline.sh",
    "configs/dcipher/crypto_planner_executor.yaml",
    "configs/dcipher/rev_planner_executor.yaml",
    "configs/single_executor/crypto_single_executor.yaml",
    "nyuctf_multiagent/backends/__init__.py",
    "nyuctf_baseline/backends/openai_backend.py",
    "nyuctf_multiagent/prompting.py",
    "nyuctf_baseline/prompts/prompts.py",
]

failed = []
for rel in files_to_check:
    path = os.path.join(ROOT, rel)
    if not os.path.exists(path):
        failed.append((rel, "MISSING"))
    else:
        try:
            if os.path.getsize(path) == 0:
                failed.append((rel, "EMPTY"))
        except OSError as e:
            failed.append((rel, f"ERROR: {e}"))

if failed:
    print("Smoke test FAILED. Problems:")
    for f, reason in failed:
        print(f" - {f}: {reason}")
    sys.exit(2)

print("Smoke test OK: all essential files present and non-empty.")
sys.exit(0)

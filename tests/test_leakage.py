"""Leakage audit exposed as pytest cases (Phase D).

Run:  python -m pytest tests/test_leakage.py -q
Each case re-runs the corresponding check and enumerates detail on failure.
Also provides `run_leakage_tests` for direct execution.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import src.leakage_audit as la  # noqa: E402


@pytest.fixture(scope="module")
def ctx():
    return la._load()


CHECK_IDS = [la.check_l1, la.check_l2, la.check_l3, la.check_l4, la.check_l5,
             la.check_l6, la.check_l7, la.check_l8, la.check_l9, la.check_l10]


@pytest.mark.parametrize("check_fn", CHECK_IDS, ids=[f.__name__ for f in CHECK_IDS])
def test_no_leakage(check_fn, ctx):
    m, imd, cells, oni = ctx
    ok, msg = check_fn(m, imd, cells=cells, oni=oni)
    assert ok, msg


if __name__ == "__main__":
    results = la.run_all()
    for r in results:
        print(f"[{'PASS' if r['ok'] else 'FAIL'}] {r['check']}: {r['message']}")
    raise SystemExit(0 if all(r["ok"] for r in results) else 1)
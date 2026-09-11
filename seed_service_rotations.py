"""
Load researched service rotations (research/service_rotations_2026_09.py)
into the service_rotations table, plus a "no_fixed_rotation" row for every
line still using the "ADHOC" label. Safe to re-run any time: everything
upserts by (shipping_line, service).

    python3 seed_service_rotations.py [--database-url ...]

Run this whenever research/*.py gains new entries -- it is NOT part of
run_pipeline.py's regular schedule, since rotations are reference data
that changes rarely, not something to re-derive every 3 hours.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import ServiceRotation, get_engine, get_session, init_db, now_utc
from research.service_rotations_2026_09 import ADHOC_LINES, ROTATIONS

JNPT_ALIASES = {"nhava sheva", "jnpt", "jawaharlal nehru port", "jawaharlal nehru"}


def _find_jnpt_index(ports: list[dict]) -> "int | None":
    for i, p in enumerate(ports):
        if p.get("port", "").strip().lower() in JNPT_ALIASES:
            return i
    return None


def _upsert(session, shipping_line: str, service: str, ports: list[dict],
            confidence: str, source_url: str, notes: str) -> str:
    shipping_line, service = shipping_line.strip().upper(), service.strip().upper()
    existing = session.query(ServiceRotation).filter_by(
        shipping_line=shipping_line, service=service,
    ).one_or_none()

    values = dict(
        ports=ports,
        jnpt_index=_find_jnpt_index(ports),
        confidence=confidence,
        source_url=source_url,
        notes=notes,
        researched_at=now_utc(),
        last_seen_in_schedule_at=now_utc(),
    )
    if existing:
        for k, v in values.items():
            setattr(existing, k, v)
        return "updated"
    session.add(ServiceRotation(shipping_line=shipping_line, service=service, **values))
    return "inserted"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL") or "sqlite:///vessel_schedule.db")
    args = parser.parse_args()

    engine = get_engine(args.database_url)
    init_db(engine)
    session = get_session(engine)

    counts = {"inserted": 0, "updated": 0}
    for r in ROTATIONS:
        outcome = _upsert(session, r["shipping_line"], r["service"], r["ports"],
                           r["confidence"], r["source_url"], r["notes"])
        counts[outcome] += 1
        found = "found" if _find_jnpt_index(r["ports"]) is not None else "NOT found"
        print(f"[{outcome}] {r['shipping_line']}/{r['service']}: "
              f"confidence={r['confidence']}, JNPT {found} in rotation")

    for line in ADHOC_LINES:
        outcome = _upsert(session, line, "ADHOC", [], "no_fixed_rotation", None,
                           "ADHOC is a JNPT-side label for an unscheduled, one-off call -- "
                           "there is no fixed rotation to research.")
        counts[outcome] += 1
        print(f"[{outcome}] {line}/ADHOC: confidence=no_fixed_rotation")

    session.commit()
    print(f"\n{counts['inserted']} inserted, {counts['updated']} updated.")


if __name__ == "__main__":
    main()

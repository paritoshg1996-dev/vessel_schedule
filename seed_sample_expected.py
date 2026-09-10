"""
Adds a handful of CLEARLY FICTIONAL "vessels expected" rows, flagged
is_sample=True, purely so the frontend's expected-vessels view (the one
with Service / Voyage / Line / Agent) has something to render.

Why fictional rather than "best effort" real data: the five terminal PDFs
could not be fetched from this build environment (see README --
jnport.gov.in isn't reachable from this sandbox's network), and the
earlier text-only inspection of those PDFs was too visually scrambled to
transcribe field-by-field without a real risk of pairing the wrong
voyage number with the wrong vessel. Shipping a guess that LOOKS like
real operational data is worse than shipping nothing -- so these rows
use obviously placeholder names and are tagged is_sample=True end to end
(DB column, JSON export, and a visible badge in the UI).

Run once for the demo:  python3 seed_sample_expected.py
Delete later with:      python3 seed_sample_expected.py --clear
"""
import argparse
import sys
from datetime import datetime, timedelta

from models import VesselSchedule, get_engine, get_session, init_db, now_utc

SAMPLE_ROWS = [
    dict(terminal_code="NSFT", berth_no=None, vessel_name="SAMPLE VESSEL ALPHA", via_no="X0001",
         service="ISA", shipping_line="MSC", agent="SAMPLE AGENCY LTD", loa_m=300.0,
         eta=now_utc() + timedelta(hours=14)),
    dict(terminal_code="NSICT", berth_no=None, vessel_name="SAMPLE VESSEL BRAVO", via_no="X0002",
         service="CIX3", shipping_line="OOCL", agent="SAMPLE AGENCY LTD", loa_m=336.0,
         eta=now_utc() + timedelta(hours=20)),
    dict(terminal_code="NSIGT", berth_no=None, vessel_name="SAMPLE VESSEL CHARLIE", via_no="X0003",
         service="FE2", shipping_line="MAERSK", agent="SAMPLE SHIPPING AGENCY", loa_m=366.0,
         eta=now_utc() + timedelta(hours=30)),
    dict(terminal_code="APMT", berth_no=None, vessel_name="SAMPLE VESSEL DELTA", via_no="X0004",
         service="JTI", shipping_line="ONE", agent="SAMPLE AGENCY LTD", loa_m=299.0,
         eta=now_utc() + timedelta(hours=9)),
    dict(terminal_code="BMCT", berth_no=None, vessel_name="SAMPLE VESSEL ECHO", via_no="X0005",
         service="AIS", shipping_line="WAN HAI", agent="SAMPLE SHIPPING AGENCY", loa_m=260.0,
         eta=now_utc() + timedelta(hours=42)),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--database-url", default="sqlite:///vessel_schedule.db")
    ap.add_argument("--clear", action="store_true", help="remove sample rows instead of adding them")
    args = ap.parse_args()

    engine = get_engine(args.database_url)
    init_db(engine)
    session = get_session(engine)

    if args.clear:
        n = session.query(VesselSchedule).filter_by(is_sample=True).delete()
        session.commit()
        print(f"Removed {n} sample rows.")
        return

    today = now_utc().date()
    added = 0
    for row in SAMPLE_ROWS:
        exists = session.query(VesselSchedule).filter_by(
            terminal_code=row["terminal_code"], via_no=row["via_no"], status="expected", report_date=today
        ).one_or_none()
        if exists:
            continue
        session.add(VesselSchedule(
            port_code="JNPT", status="expected", report_date=today,
            is_sample=True, cargo_commodity="CONTAINER", **row,
        ))
        added += 1
    session.commit()
    print(f"Added {added} sample 'expected' rows (is_sample=True).")


if __name__ == "__main__":
    sys.exit(main())

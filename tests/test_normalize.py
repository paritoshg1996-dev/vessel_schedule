import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import VesselSchedule, get_engine, get_session, init_db
from pipeline.normalize import normalize_and_upsert
from scrapers.base import ScrapedRow, ScrapeResult

TODAY = date(2026, 9, 10)


def fresh_session():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    return get_session(engine)


def make_result(rows, terminals_seen=None):
    return ScrapeResult(report_date=TODAY, rows=rows, terminals_seen=terminals_seen)


def row(section, **fields):
    return ScrapedRow(section=section, fields=fields, raw=dict(fields))


def test_no_voyage_number_does_not_collide():
    session = fresh_session()
    result = make_result([
        row("expected", terminal_code="NSFT", vessel_name="ALPHA SHIP", via_no=None),
        row("expected", terminal_code="NSFT", vessel_name="BETA SHIP", via_no=None),
    ])
    counts = normalize_and_upsert(session, 1, "JNPT", "NSFT", TODAY, result)
    assert counts["inserted"] == 2, counts
    names = {v.vessel_name for v in session.query(VesselSchedule).all()}
    assert names == {"ALPHA SHIP", "BETA SHIP"}, names
    print("PASS -- two no-voyage-number rows both kept, not collapsed into one")


def test_code_whitespace_normalized():
    session = fresh_session()
    r1 = make_result([row("expected", terminal_code="NSFT", vessel_name="GAMMA SHIP", via_no="S 1480")])
    normalize_and_upsert(session, 1, "JNPT", "NSFT", TODAY, r1)
    r2 = make_result([row("expected", terminal_code="NSFT", vessel_name="GAMMA SHIP", via_no="S1480")])
    counts = normalize_and_upsert(session, 2, "JNPT", "NSFT", TODAY, r2)
    total = session.query(VesselSchedule).count()
    assert total == 1, f"expected 1 row, got {total}"
    assert counts["updated"] == 1 and counts["inserted"] == 0, counts
    print("PASS -- 'S 1480' and 'S1480' correctly treated as the same voyage")


def test_departed_vessel_is_pruned():
    session = fresh_session()
    r1 = make_result([
        row("berthed", terminal_code="BMCT", vessel_name="SHIP ONE", via_no="S1000"),
        row("berthed", terminal_code="BMCT", vessel_name="SHIP TWO", via_no="S2000"),
    ])
    normalize_and_upsert(session, 1, "JNPT", "JNPT_MASTER", TODAY, r1, authoritative_terminals=["BMCT"])
    assert session.query(VesselSchedule).filter_by(status="berthed").count() == 2

    # SHIP ONE has sailed; today's pull only mentions SHIP TWO.
    r2 = make_result([
        row("berthed", terminal_code="BMCT", vessel_name="SHIP TWO", via_no="S2000"),
    ])
    counts = normalize_and_upsert(session, 2, "JNPT", "JNPT_MASTER", TODAY, r2, authoritative_terminals=["BMCT"])
    remaining = session.query(VesselSchedule).filter_by(status="berthed").all()
    assert [v.vessel_name for v in remaining] == ["SHIP TWO"], remaining
    assert counts["removed_stale"] == 1, counts
    print("PASS -- SHIP ONE (no longer on berth) was pruned; SHIP TWO stayed")


def test_master_reconciliation_is_scoped_per_terminal():
    """The master scraper's one run spans many terminals -- reconciling
    BMCT's berthed list must not touch NSFT's berthed rows just because
    they came from the same run. BMCT going to zero vessels is treated as
    a genuine departure here because the scraper explicitly confirms it
    still saw BMCT's (now-empty) section -- see terminals_seen below,
    and contrast with test_zero_rows_for_a_terminal_withholds_not_wipes."""
    session = fresh_session()
    r1 = make_result([
        row("berthed", terminal_code="BMCT", vessel_name="BMCT SHIP", via_no="B1"),
        row("berthed", terminal_code="NSFT", vessel_name="NSFT SHIP", via_no="N1"),
    ], terminals_seen={"BMCT", "NSFT"})
    normalize_and_upsert(session, 1, "JNPT", "JNPT_MASTER", TODAY, r1)

    # Next run: BMCT's berth section is still there (confirmed seen) but
    # empty -- the ship sailed. NSFT ship still there.
    r2 = make_result([
        row("berthed", terminal_code="NSFT", vessel_name="NSFT SHIP", via_no="N1"),
    ], terminals_seen={"BMCT", "NSFT"})
    counts = normalize_and_upsert(session, 2, "JNPT", "JNPT_MASTER", TODAY, r2)
    remaining = {v.terminal_code for v in session.query(VesselSchedule).filter_by(status="berthed").all()}
    assert remaining == {"NSFT"}, remaining
    assert counts["removed_stale"] == 1, counts
    print("PASS -- reconciliation correctly scoped per-terminal, pruned BMCT once confirmed empty")


def test_real_data_supersedes_sample():
    session = fresh_session()
    session.add(VesselSchedule(
        port_code="JNPT", terminal_code="NSICT", status="expected", report_date=TODAY,
        vessel_name="SAMPLE VESSEL BRAVO", via_no="X0002", is_sample=True,
    ))
    session.commit()
    assert session.query(VesselSchedule).filter_by(is_sample=True).count() == 1

    real = make_result([row("expected", terminal_code="NSICT", vessel_name="REAL SHIP", via_no="S9999")])
    counts = normalize_and_upsert(session, 1, "JNPT", "NSICT", TODAY, real)

    remaining = session.query(VesselSchedule).filter_by(status="expected").all()
    assert len(remaining) == 1 and remaining[0].vessel_name == "REAL SHIP", remaining
    assert counts["removed_stale"] == 1, counts
    print("PASS -- real data replaced the sample placeholder once it arrived")


def test_unobserved_terminal_section_is_left_alone():
    """Different from the departure test: here BMCT's section wasn't
    observed in the new run at all (terminals_seen doesn't include it) --
    exactly as consistent with 'parser missed BMCT's block entirely' as
    'BMCT genuinely empty'. Its existing rows must be left untouched."""
    session = fresh_session()
    r1 = make_result([
        row("berthed", terminal_code="BMCT", vessel_name="BMCT SHIP", via_no="B1"),
        row("berthed", terminal_code="NSFT", vessel_name="NSFT SHIP", via_no="N1"),
    ], terminals_seen={"BMCT", "NSFT"})
    normalize_and_upsert(session, 1, "JNPT", "JNPT_MASTER", TODAY, r1)

    # This run's terminals_seen only includes NSFT -- BMCT's section
    # itself wasn't found on the page this time (possible layout change),
    # not "found and confirmed empty". Same NSFT vessel again, unchanged.
    r2 = make_result([
        row("berthed", terminal_code="NSFT", vessel_name="NSFT SHIP", via_no="N1"),
    ], terminals_seen={"NSFT"})
    counts = normalize_and_upsert(session, 2, "JNPT", "JNPT_MASTER", TODAY, r2)

    bmct_rows = session.query(VesselSchedule).filter_by(terminal_code="BMCT", status="berthed").all()
    assert len(bmct_rows) == 1 and bmct_rows[0].vessel_name == "BMCT SHIP", bmct_rows
    assert counts["removed_stale"] == 0, counts
    print("PASS -- BMCT's existing row was left alone since its section wasn't observed this run")


if __name__ == "__main__":
    test_no_voyage_number_does_not_collide()
    test_code_whitespace_normalized()
    test_departed_vessel_is_pruned()
    test_master_reconciliation_is_scoped_per_terminal()
    test_unobserved_terminal_section_is_left_alone()
    test_real_data_supersedes_sample()
    print("\nAll normalize/dedup tests passed.")

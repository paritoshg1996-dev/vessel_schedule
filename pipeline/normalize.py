"""
Normalisation: turn staged rows into the one clean table the frontend and
any API reads from. This is deliberately the ONLY place that does string
cleanup / casing / dedup / stale-row cleanup, so "what counts as the same
vessel visit, and when is an old row no longer current" lives in exactly
one function rather than being reimplemented per terminal.

Two things worth knowing about the dedup strategy:

1. Matching key. via_no (voyage/call number) is the natural key when
   present. But a handful of rows can come through with no via_no at all
   (extraction miss, or a source that genuinely doesn't print one) --
   matching those purely on "terminal + no voyage number" would collide
   two different ships together and silently overwrite one with the
   other. So the match key falls back to vessel_name whenever via_no is
   missing, both for the DB lookup and for tracking what this batch
   touched.

2. Stale rows. A pull only tells you what's true *right now* -- if a
   vessel that was "expected" yesterday has since berthed, today's
   expected-list pull for that terminal simply won't mention it anymore.
   Nothing about an upsert-by-key removes the *old* row, so without an
   explicit cleanup step it sits in vessel_schedule forever, showing up
   as a stale "expected" entry alongside the vessel's own newer
   "berthed" row -- which reads exactly like a duplicate on the
   frontend even though the dedup key never technically collided.
   After each successful, non-empty run for a given (terminal, section),
   any previously-normalized row for that terminal+section NOT touched
   by this run is deleted -- including old sample placeholders, which is
   exactly how real data is meant to retire them. staging_raw keeps the
   full historical record if you ever need to audit past pulls; this
   table is deliberately "current state only."
"""
import re
from collections import defaultdict

from models import BerthedVessel, VesselSchedule, now_utc
from scrapers.base import ScrapedRow, ScrapeResult


def _clean_str(s):
    """For free text (vessel names, cargo) where internal spaces are real."""
    if s is None:
        return None
    s = re.sub(r"\s+", " ", str(s).strip())
    return s.upper() if s else None


def _clean_code(s):
    """For codes (voyage numbers, berth numbers) that should never contain
    whitespace -- a stray space from a parsing hiccup ("S 1480" vs "S1480")
    would otherwise look like a different voyage and create a near-duplicate."""
    if s is None:
        return None
    s = re.sub(r"\s+", "", str(s).strip())
    return s.upper() if s else None


def normalize_and_upsert(session, run_id: int, port_code: str, terminal_code: str,
                          report_date, result: ScrapeResult, is_sample: bool = False,
                          authoritative_terminals=None) -> dict:
    """Returns counts: {'inserted', 'updated', 'skipped', 'removed_stale'}.

    authoritative_terminals: which terminal_codes this run speaks for, for
    reconciliation purposes. Defaults to result.terminals_seen when the
    scraper set one (the master scraper does -- see jnpa_master.py), else
    just `terminal_code` (correct for the single-terminal PDF scrapers,
    which only ever speak for themselves). Pass this explicitly only to
    override that default (mainly useful in tests).
    """
    counts = {"inserted": 0, "updated": 0, "skipped": 0, "removed_stale": 0}
    now = now_utc()
    touched_ids = defaultdict(set)  # (terminal_code, section) -> {row ids}
    if authoritative_terminals is not None:
        authoritative_terminals = set(authoritative_terminals)
    elif result.terminals_seen is not None:
        authoritative_terminals = set(result.terminals_seen)
    else:
        authoritative_terminals = {terminal_code}

    for row in result.rows:
        f = row.fields
        vessel_name = _clean_str(f.get("vessel_name"))
        via_no = _clean_code(f.get("via_no"))
        row_terminal_code = f.get("terminal_code") or terminal_code

        if not vessel_name and not via_no:
            counts["skipped"] += 1
            continue

        match = dict(terminal_code=row_terminal_code, status=row.section, report_date=report_date)
        if via_no:
            match["via_no"] = via_no
        else:
            match["via_no"] = None
            match["vessel_name"] = vessel_name  # fallback key so two no-voyage-number
                                                  # rows in the same batch don't collide

        existing = session.query(VesselSchedule).filter_by(**match).one_or_none()

        values = dict(
            port_code=port_code,
            terminal_code=row_terminal_code,
            berth_no=_clean_code(f.get("berth_no")),
            status=row.section,
            vessel_name=vessel_name or "UNKNOWN",
            via_no=via_no,
            service=_clean_str(f.get("service")),
            shipping_line=_clean_str(f.get("shipping_line")),
            agent=_clean_str(f.get("agent")),
            loa_m=f.get("loa_m"),
            cargo_commodity=_clean_str(f.get("cargo_commodity")),
            eta=f.get("eta"),
            gate_cutoff=f.get("gate_cutoff"),
            berthed_on=f.get("berthed_on"),
            expected_completion=f.get("expected_completion"),
            sailed_on=f.get("sailed_on"),
            report_date=report_date,
            source_run_id=run_id,
            last_seen_at=now,
            is_sample=is_sample,
        )

        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            row_obj = existing
            counts["updated"] += 1
        else:
            row_obj = VesselSchedule(first_seen_at=now, **values)
            session.add(row_obj)
            session.flush()  # assign an id so it can be tracked below
            counts["inserted"] += 1

        touched_ids[(row_terminal_code, row.section)].add(row_obj.id)

    # Reconciliation: this run speaks authoritatively for every section it
    # reported, across every terminal in authoritative_terminals -- not
    # just the terminals that happened to have a row this time. That's
    # what lets a vessel that's genuinely gone quiet (sailed, or dropped
    # off an expected list) get pruned even when it was the *only* thing
    # missing from an otherwise-normal run.
    #
    # The safety net against a parsing regression wiping real data isn't
    # a special case here -- it's that authoritative_terminals only ever
    # contains terminals we can actually confirm we looked at this run
    # (the master scraper's terminals_seen; a single-terminal PDF
    # scraper's own code, since reaching this function at all means its
    # own fetch+parse succeeded). A terminal whose section silently
    # vanished from a source's layout is never added to that set in the
    # first place, so it's simply never considered here -- its existing
    # rows are left alone by construction, not by a bolt-on exception.
    sections_reported = set(section for (_, section) in touched_ids.keys())
    for t_code in authoritative_terminals:
        for section in sections_reported:
            touched = touched_ids.get((t_code, section), set())
            existing_rows = session.query(VesselSchedule).filter_by(
                terminal_code=t_code, status=section,
            ).all()
            for s in existing_rows:
                if s.id not in touched:
                    session.delete(s)
                    counts["removed_stale"] += 1

    session.commit()
    return counts


def normalize_and_upsert_berthed(session, run_id: int, port_code: str, terminal_code: str,
                                  report_date, berthed_rows: list[ScrapedRow]) -> dict:
    """Same upsert-by-key + stale-row-reconciliation shape as
    `normalize_and_upsert`, targeting `berthed_vessels` instead. Simpler
    than that function in one respect: every caller here is a single
    per-terminal PDF scraper reporting only on its own berths, so there's
    no cross-terminal `authoritative_terminals` question -- a successful
    call always speaks authoritatively for `terminal_code`'s berthed rows
    this run, full stop.
    """
    counts = {"inserted": 0, "updated": 0, "skipped": 0, "removed_stale": 0}
    now = now_utc()
    touched_ids = set()

    for row in berthed_rows:
        f = row.fields
        vessel_name = _clean_str(f.get("vessel_name"))
        via_no = _clean_code(f.get("via_no"))

        if not vessel_name and not via_no:
            counts["skipped"] += 1
            continue

        match = dict(terminal_code=terminal_code, report_date=report_date)
        if via_no:
            match["via_no"] = via_no
        else:
            match["via_no"] = None
            match["vessel_name"] = vessel_name  # fallback key, same reasoning as
                                                  # normalize_and_upsert above

        existing = session.query(BerthedVessel).filter_by(**match).one_or_none()

        values = dict(
            port_code=port_code,
            terminal_code=terminal_code,
            berth_no=_clean_code(f.get("berth_no")),
            vessel_name=vessel_name or "UNKNOWN",
            via_no=via_no,
            service=_clean_str(f.get("service")),
            shipping_line=_clean_str(f.get("shipping_line")),
            loa_m=f.get("loa_m"),
            draft_m=f.get("draft_m"),
            side=_clean_str(f.get("side")),
            alongside_at=f.get("alongside_at"),
            ops_commenced_at=f.get("ops_commenced_at"),
            ops_completed_at=f.get("ops_completed_at"),
            next_event_at=f.get("next_event_at"),
            import_moves=f.get("import_moves"),
            export_moves=f.get("export_moves"),
            report_date=report_date,
            source_run_id=run_id,
            last_seen_at=now,
        )

        if existing:
            for k, v in values.items():
                setattr(existing, k, v)
            row_obj = existing
            counts["updated"] += 1
        else:
            row_obj = BerthedVessel(first_seen_at=now, **values)
            session.add(row_obj)
            session.flush()
            counts["inserted"] += 1

        touched_ids.add(row_obj.id)

    existing_rows = session.query(BerthedVessel).filter_by(terminal_code=terminal_code).all()
    for s in existing_rows:
        if s.id not in touched_ids:
            session.delete(s)
            counts["removed_stale"] += 1

    session.commit()
    return counts

"""
Load researched service rotations (research/service_rotations_*.py) into
the service_rotations table, plus a "no_fixed_rotation" row for every
line still using the "ADHOC" label. Safe to re-run any time: everything
upserts by (shipping_line, service, direction).

    python3 seed_service_rotations.py [--database-url ...]

Run this whenever a research/*.py file gains new entries -- it is NOT
part of run_pipeline.py's regular schedule, since rotations are
reference data that changes rarely, not something to re-derive every
3 hours.
"""
import argparse
import glob
import importlib.util
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import ServiceRotation, get_engine, get_session, init_db, now_utc

JNPT_ALIASES = {"nhava sheva", "jnpt", "jawaharlal nehru port", "jawaharlal nehru"}

# Carrier names decoded from the abbreviation vessel_schedule.shipping_line
# actually holds, built up from what each service-rotation search turned
# up along the way (e.g. searching "CCA ... BIGEX" kept surfacing CMA
# CGM's own pages). Deliberately incomplete: a code with no confident
# match anywhere in that research is left OUT of this dict rather than
# guessed, and comes through as shipping_line_name=NULL -- same "don't
# guess" discipline as the rotations themselves. A couple of these are
# still genuinely uncertain even where a name IS recorded; see the
# specific ServiceRotation row's own `notes` for that (e.g. "EGI").
CARRIER_NAMES = {
    "MSC": "Mediterranean Shipping Company (MSC)",
    "MAE": "Maersk",
    "MSK": "Maersk",
    "CCA": "CMA CGM",
    "HLI": "Hapag-Lloyd",
    "WHI": "Wan Hai Lines",
    "WHL": "Wan Hai Lines",
    "COS": "COSCO Shipping Lines",
    "PIL": "Pacific International Lines",
    "ISL": "Interasia Lines",
    "OCL": "OOCL (Orient Overseas Container Line)",
    "ONE": "Ocean Network Express",
    "HMM": "HMM (Hyundai Merchant Marine)",
    "CUL": "CU Lines",
    "GSL": "Gold Star Line",
    "RCL": "Regional Container Lines",
    "KMD": "KMTC (Korea Marine Transport Co.)",
    "ESA": "Emirates Shipping Line",
    "UNF": "Unifeeder",
    "SEC": "X-Press Feeders (Sea Consortium)",
    # Found via CSX/CISC (Emirates Shipping Line's own launches) but
    # EGI/AGI's research pointed to Evergreen instead -- genuinely
    # ambiguous, not a typo. See that row's own `notes`.
    "EGI": "Emirates Shipping Line (unconfirmed -- possibly Evergreen instead, see notes)",
}


def _find_jnpt_index(ports: list[dict]) -> "int | None":
    for i, p in enumerate(ports):
        if p.get("port", "").strip().lower() in JNPT_ALIASES:
            return i
    return None


def _upsert(session, shipping_line: str, service: str, direction: str, ports: list[dict],
            confidence: str, source_url: str, notes: str) -> str:
    shipping_line, service = shipping_line.strip().upper(), service.strip().upper()
    direction = (direction or "single").strip().lower()
    existing = session.query(ServiceRotation).filter_by(
        shipping_line=shipping_line, service=service, direction=direction,
    ).one_or_none()

    values = dict(
        shipping_line_name=CARRIER_NAMES.get(shipping_line),
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
    session.add(ServiceRotation(shipping_line=shipping_line, service=service,
                                 direction=direction, **values))
    return "inserted"


def _load_research_modules():
    """Every research/service_rotations_*.py file, each exposing ROTATIONS
    and (optionally) ADHOC_LINES -- lets research get split across dated
    files as it accumulates rather than one ever-growing module."""
    modules = []
    here = os.path.dirname(os.path.abspath(__file__))
    for path in sorted(glob.glob(os.path.join(here, "research", "service_rotations_*.py"))):
        name = os.path.splitext(os.path.basename(path))[0]
        spec = importlib.util.spec_from_file_location(f"research.{name}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        modules.append(mod)
    return modules


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL") or "sqlite:///vessel_schedule.db")
    args = parser.parse_args()

    engine = get_engine(args.database_url)
    init_db(engine)
    session = get_session(engine)

    counts = {"inserted": 0, "updated": 0}
    seen_adhoc_lines = set()
    for mod in _load_research_modules():
        for r in getattr(mod, "ROTATIONS", []):
            outcome = _upsert(session, r["shipping_line"], r["service"], r.get("direction", "single"),
                               r["ports"], r["confidence"], r["source_url"], r["notes"])
            counts[outcome] += 1
            found = "found" if _find_jnpt_index(r["ports"]) is not None else "NOT found"
            print(f"[{outcome}] {r['shipping_line']}/{r['service']}/{r.get('direction','single')}: "
                  f"confidence={r['confidence']}, JNPT {found}")
        for line in getattr(mod, "ADHOC_LINES", []):
            if line in seen_adhoc_lines:
                continue
            seen_adhoc_lines.add(line)
            outcome = _upsert(session, line, "ADHOC", "single", [], "no_fixed_rotation", None,
                               "ADHOC is a JNPT-side label for an unscheduled, one-off call -- "
                               "there is no fixed rotation to research.")
            counts[outcome] += 1
            print(f"[{outcome}] {line}/ADHOC: confidence=no_fixed_rotation")

    session.commit()
    print(f"\n{counts['inserted']} inserted, {counts['updated']} updated.")
    unnamed = sorted(set(r.shipping_line for r in session.query(ServiceRotation).all()
                          if not r.shipping_line_name))
    if unnamed:
        print(f"Shipping lines with no decoded name on record ({len(unnamed)}): {', '.join(unnamed)}")


if __name__ == "__main__":
    main()

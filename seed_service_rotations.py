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
# actually holds. Primary source: JNPA's own official "List of Shipping
# Agencies Registered" (https://www.jnport.gov.in/page/list-of-shipping-
# agencies-registered/..., PDF at .../uploads/content_manager/
# shipping_Agencies.pdf) -- a Sr.No./Id/Name/SCAC/BIC table of every
# agency registered at the port. Our `shipping_line` values are that
# registry's own codes with the trailing digit stripped (e.g. registry
# "EGI1" -> our "EGI"), which is what let this resolve a prior mistake:
# EGI was earlier guessed as Emirates Shipping Line from circumstantial
# pattern-matching (CSX/CISC rotations found via Emirates' own press
# releases); the registry instead lists EGI1 as "EVERGREEN SHIPPING
# AGENCY (INDIA)" -- confirmed here as Evergreen. The CSX/CISC rotation
# data itself is left as originally recorded (still plausible if
# Evergreen also holds a slot on that consortium loop), just re-flagged.
#
# A handful of codes here (MAE, WHL, COS, ISL, CUL, TSC) don't have an
# exact match in the registry under that precise code, but were kept
# from the earlier round of research (global SCAC conventions / strong
# contextual matches from the rotation searches themselves) with a note
# added below -- everything else in this dict is a direct registry hit.
# A code with no confident match ANYWHERE (registry included) is left
# OUT of this dict rather than guessed, and comes through as
# shipping_line_name=NULL -- same "don't guess" discipline as the
# rotations themselves.
CARRIER_NAMES = {
    "MSC": "Mediterranean Shipping Company (MSC)",  # registry: MSC1 "MSC AGENCY INDIA PVT LTD"
    "MSK": "Maersk",  # registry: MSK3 "MAERSK LINE INDIA PVT LTD"
    "MAE": "Maersk (not found under this exact code in the registry, which lists Maersk as MSK3 -- kept via Maersk's global SCAC 'MAEU')",
    "CCA": "CMA CGM",  # registry: CCA1 "CMA CGM AGENCIES (I) PLTD-A/C CMA"
    "HLI": "Hapag-Lloyd",  # registry: HLI1 "HAPAG LLOYD INDIA PVT LTD"
    "WHI": "Wan Hai Lines",  # registry: WHI1 "WAN HAI LINES (INDIA) PVT LTD"
    "WHL": "Wan Hai Lines (not found under this exact code in the registry, which lists Wan Hai as WHI1 -- kept from context: paired with WHI/WHI1 across the CI6/SI8 consortium research)",
    "OCL": "OOCL (Orient Overseas Container Line)",  # registry: OCL1 "OOCL(ORIENT OVERSEAS CONTR LINES)"
    "ONE": "Ocean Network Express",  # registry: ONE1 "ONE (OCEAN NETWORK EXPRESS) LINE"
    "HMM": "HMM (Hyundai Merchant Marine)",  # registry: HMM1 "HYUNDAI MERCHANT MARINE INDIA P LTD" -- exact match
    "PIL": "Pacific International Lines",  # registry: PIL4/PIL2 "PIL (INDIA)"/"PIL MUMBAI"
    "ISL": "Interasia Lines (registry lists Interasia's own code as INA1, not ISL -- kept from strong vessel-name evidence, e.g. 'INTERASIA ACCLERATE'/'INTERASIA TRANSCEND')",
    "COS": "COSCO Shipping Lines (registry lists COSCO's own code as CSP1/CSP3, not COS -- kept from the AGI2 research, which independently confirmed COSCO as the operator)",
    "CUL": "CU Lines (registry's own 'CUL1' entry is actually the local AGENT 'SEAHORSE SHIP AGENCIES PVT LTD' representing this principal, not a company literally named CU Lines -- kept the carrier brand name since that's what the rotation research found operating the IMR service)",
    "GSL": "Gold Star Line",  # registry: GLD1 "STAR SHIPPING SERVICE (I) P LTD-GSL" -- explicitly named as GSL's own agent
    "RCL": "Regional Container Lines",  # registry: RCL2/RCA1 "RCL AGENCIES (INDIA)"
    "KMD": "KMTC (Korea Marine Transport Co.)",  # registry: KMD1 "KMTC ( India ) PVT. LTD." -- exact match
    "ESA": "Emirates Shipping Agencies (India)",  # registry: ESA1 "EMIRATES SHIPPING AGENCIES(I) P LTD" -- exact match
    "UNF": "Unifeeder",  # registry: UNF1 "UNIFEEDER AGENCIES INDIA PVT LTD" -- exact match
    "SEC": "X-Press Feeders (Sea Consortium Shipping India)",  # registry: SEC1 "SEA CONSORTIUM SHIPPING (INDIA)" -- exact match
    "EGI": "Evergreen Line (Evergreen Shipping Agency India)",  # registry: EGI1 "EVERGREEN SHIPPING AGENCY (INDIA)" --
                                  # exact match; corrects an earlier guess of "Emirates Shipping Line"
    "DMA": "Diamond Maritime Agency",  # registry: DMA3 "DIAMOND MARITIME AGENCY PVT. LTD." -- exact match
    "ECL": "Evershine Container Line",  # registry: ECL3 "EVERSHINE CONTAINER LINE PRIVATE LIMITED" -- exact match
    "EMS": "Efficient Marine Services",  # registry: EMS1 "EFFICIENT MARINE SERVICES LLP" -- exact match
    "KIN": "Kin-Ship Services (India)",  # registry: KIN1 "KIN-SHIP SERVICES (INDIA) PVT LTD" -- exact match
    "PMA": "Parekh Marine Agencies",  # registry: PMA1/PMA3 "PAREKH MARINE AGENCIES/SERVICES" -- exact match
    "SMM": "Sima Marine (India)",  # registry: SMM3 "SIMA MARINE (INDIA) PVT LTD" -- exact match
    "TNS": "Transnational Shipping India",  # registry: TNS1 "TRANSNATIONAL SHIPPING INDIA PVT LTD" -- exact match
    "MIL": "Poseidon Shipping Agency",  # registry: MIL1 "POSEIDON SHIPPING AGENCY PVT LTD" -- exact match
    "CSS": "Combined Shipping Services",  # registry: CSS1 "COMBINED SHIPPING SERVICES PVT LTD" -- exact match
    "MBK": "MBK Logistix",  # registry: MBK1 "MBK LOGISTIX PVT LTD" -- exact match
    "TSC": "T.S. Lines (registry's own code for this carrier appears to be TSI, not TSC exactly -- close enough to flag as likely the same, not confirmed)",
    # AKS, EMT, RGS, SBB, SMD, TST, WAN: no confident match found anywhere,
    # registry included ("TST2" in the registry is a dummy/test entry, not
    # a real carrier) -- deliberately absent from this dict.
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

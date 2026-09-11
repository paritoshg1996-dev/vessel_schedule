"""
Mirrors the current, already-reconciled state of vessel_schedule and
berthed_vessels into MongoDB, for a downstream app backend (e.g. a FastAPI
service reading these same collections) to serve over its own API.

Deliberately NOT an incremental sync: SQL is still the one place dedup,
reconciliation, and stale-row cleanup happen (see pipeline/normalize.py's
docstring for why that matters). By the time this runs, `session` already
holds the definitive current state for both tables, so each collection is
just fully replaced with whatever SQL currently says is true -- no upsert
logic, no second copy of the reconciliation rules to keep in sync with the
first. At this data volume (a few hundred rows) a full delete+insert every
~3 hours is cheap and, more importantly, can't drift from SQL over time the
way an incremental mirror eventually would.

Field names match the REST API built on top of this (GET /api/vessels/
expected, /berthed, /meta in the container_traffic backend) -- if you
rename a field here, update that backend's routes to match.
"""
from datetime import date, datetime

from pymongo import MongoClient

from models import BerthedVessel, IngestionRun, VesselSchedule


def _jsonable(value):
    """MongoDB/BSON has no plain `date` type, only `datetime` -- promote
    one to midnight UTC rather than passing it through as an unsupported
    type pymongo would otherwise raise on."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)
    return value


def _vessel_schedule_doc(v: VesselSchedule) -> dict:
    return {
        "port_code": v.port_code,
        "terminal_code": v.terminal_code,
        "berth_no": v.berth_no,
        "status": v.status,
        "vessel_name": v.vessel_name,
        "via_no": v.via_no,
        "service": v.service,
        "shipping_line": v.shipping_line,
        "agent": v.agent,
        "loa_m": v.loa_m,
        "cargo_commodity": v.cargo_commodity,
        "eta": _jsonable(v.eta),
        "gate_cutoff": _jsonable(v.gate_cutoff),
        "berthed_on": _jsonable(v.berthed_on),
        "expected_completion": _jsonable(v.expected_completion),
        "sailed_on": _jsonable(v.sailed_on),
        "report_date": _jsonable(v.report_date),
        "is_sample": v.is_sample,
    }


def _berthed_vessel_doc(b: BerthedVessel) -> dict:
    return {
        "port_code": b.port_code,
        "terminal_code": b.terminal_code,
        "berth_no": b.berth_no,
        "vessel_name": b.vessel_name,
        "via_no": b.via_no,
        "service": b.service,
        "shipping_line": b.shipping_line,
        "loa_m": b.loa_m,
        "draft_m": b.draft_m,
        "side": b.side,
        "alongside_at": _jsonable(b.alongside_at),
        "ops_commenced_at": _jsonable(b.ops_commenced_at),
        "ops_completed_at": _jsonable(b.ops_completed_at),
        "next_event_at": _jsonable(b.next_event_at),
        "import_moves": b.import_moves,
        "export_moves": b.export_moves,
        "report_date": _jsonable(b.report_date),
    }


def export_to_mongo(session, mongo_url: str, db_name: str, terminals_meta: dict) -> dict:
    """Replace vessel_schedule/berthed_vessels/vessel_schedule_meta in the
    target Mongo database with the current SQL state. Returns counts for
    logging. Raises on a connection/write failure -- the caller decides
    whether that should fail the whole pipeline run or just get logged
    (see run_pipeline.py)."""
    client = MongoClient(mongo_url, serverSelectionTimeoutMS=10_000)
    try:
        db = client[db_name]

        schedule_docs = [_vessel_schedule_doc(v) for v in session.query(VesselSchedule).all()]
        berthed_docs = [_berthed_vessel_doc(b) for b in session.query(BerthedVessel).all()]

        db.vessel_schedule.delete_many({})
        if schedule_docs:
            db.vessel_schedule.insert_many(schedule_docs)

        db.berthed_vessels.delete_many({})
        if berthed_docs:
            db.berthed_vessels.insert_many(berthed_docs)

        latest_runs = (
            session.query(IngestionRun)
            .order_by(IngestionRun.terminal_code, IngestionRun.started_at.desc())
            .all()
        )
        seen, run_status = set(), []
        for r in latest_runs:
            if r.terminal_code in seen:
                continue
            seen.add(r.terminal_code)
            run_status.append({
                "terminal_code": r.terminal_code,
                "terminal_name": terminals_meta.get(r.terminal_code, {}).get("terminal_name", r.terminal_code),
                "status": r.status,
                "rows_found": r.rows_found,
                "report_date": _jsonable(r.report_date),
                "started_at": _jsonable(r.started_at),
                "error_type": r.error_type,
                "error_message": r.error_message,
            })
        db.vessel_schedule_meta.replace_one(
            {"_id": "latest"},
            {"_id": "latest", "generated_at": datetime.utcnow(), "run_status": run_status},
            upsert=True,
        )

        return {"vessel_schedule": len(schedule_docs), "berthed_vessels": len(berthed_docs)}
    finally:
        client.close()

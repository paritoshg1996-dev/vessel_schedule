"""
Run every registered source once: fetch -> parse -> stage -> normalise ->
alert-check. Meant to be invoked on a schedule (cron / GitHub Actions --
see .github/workflows/scrape.yml) with plain `python run_pipeline.py`.

    python run_pipeline.py                          # all-live (production)
    python run_pipeline.py --master-fixture PATH     # demo/test: master page
                                                      # read from a local file
                                                      # instead of the network;
                                                      # terminal PDFs still
                                                      # attempt live fetch.

Every run, live or fixture-backed, writes a real ingestion_runs row and
runs the real alert checks -- there's no separate "demo alerting," which
is the point: you want the exact code path that fires at 3am to be the
one you're looking at right now.
"""
import argparse
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import BerthedVessel, IngestionRun, Terminal, VesselSchedule, get_engine, get_session, init_db, now_utc
from pipeline.alerts import check_and_raise_alerts, notify_admin
from pipeline.normalize import normalize_and_upsert, normalize_and_upsert_berthed
from pipeline.staging import stage_scrape_result
from scrapers import SCRAPER_CLASSES
from scrapers.base import FetchError, ParseError, ScrapeResult
from scrapers.jnpa_master import JnpaMasterScraper
from scrapers.registry import TERMINALS


def ensure_terminals_seeded(session):
    if session.query(Terminal).count() == 0:
        for t in TERMINALS:
            session.add(Terminal(**t))
        session.commit()


def run_one_scraper(session, terminal_code: str, scope: str, scraper) -> IngestionRun:
    run = IngestionRun(terminal_code=terminal_code, scope=scope, status="running")
    session.add(run)
    session.commit()

    try:
        result = scraper.run()
        run.report_date = result.report_date
        run.rows_found = len(result.rows)
        run.status = "success"
        run.finished_at = now_utc()
        session.commit()

        stage_scrape_result(session, run.id, terminal_code, result)

        port_code = next((t["port_code"] for t in TERMINALS if t["terminal_code"] == terminal_code), "JNPT")
        if result.report_date:
            if scope == "terminal":
                # A terminal's own PDF may report vessels currently alongside
                # its berths too -- route those to their own table
                # (models.BerthedVessel) rather than vessel_schedule, which
                # already gets a (thinner) 'berthed' status from the JNPA
                # master page's own scrape. Keeping the two separate means
                # neither one can overwrite or collide with the other.
                schedule_rows = [r for r in result.rows if r.section != "berthed"]
                berthed_rows = [r for r in result.rows if r.section == "berthed"]
                schedule_result = ScrapeResult(
                    report_date=result.report_date, rows=schedule_rows,
                    discovered_links=result.discovered_links,
                    terminals_seen=result.terminals_seen,
                )
                normalize_and_upsert(session, run.id, port_code, terminal_code,
                                      result.report_date, schedule_result)
                normalize_and_upsert_berthed(session, run.id, port_code, terminal_code,
                                              result.report_date, berthed_rows)
            else:
                # The master page (scope == "master") only ever reports
                # 'berthed' rows -- now that each terminal's own PDF feeds
                # berthed_vessels directly (above), we don't want the
                # master page's thinner version in vessel_schedule too.
                # Its report_date/discovered_links/rows_found still drive
                # link discovery and the alert checks above and below;
                # it just no longer writes anything to vessel_schedule.
                pass

        return run, result

    except FetchError as e:
        run.status = "failed"
        run.error_type = "network"
        run.error_message = str(e)
        run.finished_at = now_utc()
        session.commit()
        return run, None

    except ParseError as e:
        run.status = "failed"
        run.error_type = "parse"
        run.error_message = str(e)
        run.finished_at = now_utc()
        session.commit()
        return run, None

    except Exception as e:  # belt and braces -- an unexpected bug shouldn't kill the whole run either
        run.status = "failed"
        run.error_type = "unexpected"
        run.error_message = f"{type(e).__name__}: {e}"
        run.finished_at = now_utc()
        session.commit()
        return run, None


def export_data_json(session, out_path: str):
    schedule_rows = (
        session.query(VesselSchedule)
        .order_by(VesselSchedule.status, VesselSchedule.eta.is_(None), VesselSchedule.eta)
        .all()
    )
    berthed_rows = (
        session.query(BerthedVessel)
        .order_by(BerthedVessel.terminal_code, BerthedVessel.berth_no)
        .all()
    )
    latest_runs = (
        session.query(IngestionRun)
        .order_by(IngestionRun.terminal_code, IngestionRun.started_at.desc())
        .all()
    )
    seen_terminals = set()
    run_status = []
    for r in latest_runs:
        if r.terminal_code in seen_terminals:
            continue
        seen_terminals.add(r.terminal_code)
        run_status.append({
            "terminal_code": r.terminal_code,
            "scope": r.scope,
            "status": r.status,
            "rows_found": r.rows_found,
            "report_date": r.report_date.isoformat() if r.report_date else None,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "error_type": r.error_type,
            "error_message": r.error_message,
        })

    terminals_meta = {t["terminal_code"]: t for t in TERMINALS}

    def row_to_dict(v: VesselSchedule):
        return {
            "port_code": v.port_code,
            "terminal_code": v.terminal_code,
            "terminal_name": terminals_meta.get(v.terminal_code, {}).get("terminal_name", v.terminal_code),
            "berth_no": v.berth_no,
            "status": v.status,
            "vessel_name": v.vessel_name,
            "via_no": v.via_no,
            "service": v.service,
            "shipping_line": v.shipping_line,
            "agent": v.agent,
            "loa_m": v.loa_m,
            "cargo_commodity": v.cargo_commodity,
            "eta": v.eta.isoformat() if v.eta else None,
            "gate_cutoff": v.gate_cutoff.isoformat() if v.gate_cutoff else None,
            "berthed_on": v.berthed_on.isoformat() if v.berthed_on else None,
            "expected_completion": v.expected_completion.isoformat() if v.expected_completion else None,
            "sailed_on": v.sailed_on.isoformat() if v.sailed_on else None,
            "report_date": v.report_date.isoformat() if v.report_date else None,
            "is_sample": v.is_sample,
        }

    def berthed_to_dict(b: BerthedVessel):
        return {
            "port_code": b.port_code,
            "terminal_code": b.terminal_code,
            "terminal_name": terminals_meta.get(b.terminal_code, {}).get("terminal_name", b.terminal_code),
            "berth_no": b.berth_no,
            "vessel_name": b.vessel_name,
            "via_no": b.via_no,
            "service": b.service,
            "shipping_line": b.shipping_line,
            "loa_m": b.loa_m,
            "draft_m": b.draft_m,
            "side": b.side,
            "alongside_at": b.alongside_at.isoformat() if b.alongside_at else None,
            "ops_commenced_at": b.ops_commenced_at.isoformat() if b.ops_commenced_at else None,
            "ops_completed_at": b.ops_completed_at.isoformat() if b.ops_completed_at else None,
            "next_event_at": b.next_event_at.isoformat() if b.next_event_at else None,
            "import_moves": b.import_moves,
            "export_moves": b.export_moves,
            "report_date": b.report_date.isoformat() if b.report_date else None,
        }

    payload = {
        "generated_at": now_utc().isoformat() + "Z",
        "run_status": run_status,
        "vessels": [row_to_dict(v) for v in schedule_rows],
        "berthed_vessels": [berthed_to_dict(b) for b in berthed_rows],
    }
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    return payload


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", "sqlite:///vessel_schedule.db"))
    parser.add_argument("--master-fixture", default=None,
                         help="Read the JNPA master page from a local file instead of the network "
                              "(demo/test only -- omit this in production).")
    parser.add_argument("--out", default="frontend/data.json")
    parser.add_argument("--staleness-tolerance-days", type=int, default=0)
    parser.add_argument("--only", default=None,
                         help="Comma-separated terminal codes to run, e.g. --only NSICT,BMCT "
                              "(always runs JNPT_MASTER too, for link discovery). Useful for "
                              "validating one parser at a time against the live site.")
    args = parser.parse_args()
    only = set(c.strip().upper() for c in args.only.split(",")) if args.only else None

    engine = get_engine(args.database_url)
    init_db(engine)
    session = get_session(engine)
    ensure_terminals_seeded(session)

    all_new_alerts = []

    # 1) Master page first -- gives us the freshest per-terminal PDF links.
    master_scraper = JnpaMasterScraper(fixture_path=args.master_fixture)
    master_run, master_result = run_one_scraper(session, "JNPT_MASTER", "master", master_scraper)
    all_new_alerts += check_and_raise_alerts(session, master_run, args.staleness_tolerance_days)
    discovered_links = master_result.discovered_links if master_result else {}

    print(f"[JNPT_MASTER] status={master_run.status} rows={master_run.rows_found} "
          f"report_date={master_run.report_date} error={master_run.error_message}")

    # 2) Each container terminal's own PDF -- prefer today's freshly-discovered
    #    link over the (potentially stale) URL hardcoded in the registry.
    terminal_meta = {t["terminal_code"]: t for t in TERMINALS}
    for code, scraper_cls in SCRAPER_CLASSES.items():
        if code == "JNPT_MASTER":
            continue
        if only and code not in only:
            continue
        url = discovered_links.get(code) or terminal_meta[code]["source_url"]
        scraper = scraper_cls(url=url)
        run, result = run_one_scraper(session, code, "terminal", scraper)
        all_new_alerts += check_and_raise_alerts(session, run, args.staleness_tolerance_days)
        print(f"[{code}] status={run.status} rows={run.rows_found} "
              f"report_date={run.report_date} error={run.error_message}")

    if all_new_alerts:
        notify_admin(all_new_alerts, context=f"pipeline run at {now_utc().isoformat()}Z")
    else:
        print("\nNo alerts raised this run.")

    payload = export_data_json(session, args.out)
    print(f"\nExported {len(payload['vessels'])} vessel_schedule rows to {args.out}")

    session.close()


if __name__ == "__main__":
    main()

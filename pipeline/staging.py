"""
Staging: write what we scraped, close to verbatim, before any cleaning.

Keeping this step separate from normalisation matters for exactly the
failure mode this project is worried about: if a terminal changes its
PDF layout and our field-mapping breaks, staging_raw still has the
original scraped values (whatever the engine's header-snap produced)
tagged to the run that produced them. That's what you'd diff against the
previous day's staging rows to see a format change, even before anyone
updates the normalisation code to match it.
"""
import json

from models import StagingRaw
from scrapers.base import ScrapeResult


def stage_scrape_result(session, run_id: int, terminal_code: str, result: ScrapeResult) -> int:
    count = 0
    for row in result.rows:
        raw_clean = {k: v for k, v in row.raw.items() if not k.startswith("_")}
        session.add(StagingRaw(
            run_id=run_id,
            terminal_code=terminal_code,
            section=row.section,
            raw_row_json=json.dumps(raw_clean, default=str),
        ))
        count += 1
    session.commit()
    return count

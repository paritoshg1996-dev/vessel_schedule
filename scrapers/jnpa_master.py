"""
JNPA's own aggregator page: https://www.jnport.gov.in/page/daily-berthing-report/...

This is an ordinary server-rendered HTML <table>, one row per berth, under
a heading "Daily Berthing Report as on DD-MM-YYYY" -- much friendlier than
the per-terminal PDFs. We use it for two things:

1. Its own report-date heading is exactly what the freshness/"is this as
   of today" check reads, and a zero-row page is a real signal (link
   discovery below failed or the page itself is broken) worth alerting
   on -- so this scraper still parses every berth row into a ScrapedRow
   the same as before.
2. Discovering each terminal's *current* PDF report URL. The filename
   encodes the date (e.g. "..._9_9_2026.pdf") and changes daily, so
   hardcoding yesterday's URL in the registry would silently go stale --
   this page is scraped first, every run, to find today's real link.

Its rows are NOT written to vessel_schedule any more (run_pipeline.py
deliberately skips that step for this scraper's scope=="master" result).
Each terminal's own PDF now feeds a richer, terminal-native version of
the same "who's on berth right now" information straight into
models.BerthedVessel -- see that table's docstring -- so this page's
thinner one (no berth side, no ops timestamps) would only ever be a
second, less detailed copy of the same thing. Kept parsing the rows
anyway rather than dropping them entirely: rows_found staying meaningful
here is what makes the ZERO_ROWS alert check still catch a broken/empty
master page.

The terminal column is only printed on the first berth row of each group
and left blank on the rows below it in the source table -- we forward-fill
it, same as reading the printed report by eye.
"""
import re
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Comment

from scrapers.base import FetchError, ParseError, ScrapedRow, ScrapeResult, TerminalScraper

BASE_URL = "https://www.jnport.gov.in"

# Map the link text JNPA uses for each terminal's report to our terminal_code.
LINK_TEXT_TO_TERMINAL = {
    "NSFT DAILY REPORT": "NSFT",
    "NSICT REPORT": "NSICT",
    "NSIGT REPORT": "NSIGT",
    "APMT MUMBAI DAILY REPORT": "APMT",
    "BMCT REPORT": "BMCT",
    "BPCL REPORT": "BPCL",
    "JJLT REPORT": "JJLT",
    "NSDT REPORT": "NSDT",
}


def _parse_dt(date_str: str, time_str: str = "") -> datetime | None:
    raw = f"{date_str} {time_str}".strip()
    if not raw:
        return None
    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


class JnpaMasterScraper(TerminalScraper):
    terminal_code = "JNPT_MASTER"
    scope = "master"

    def __init__(self, url: str = None, fixture_path: str = None):
        self.url = url or "https://www.jnport.gov.in/page/daily-berthing-report/M2VlS0pwUXZ3akhSV0E0RDFUVlhxQT09"
        self.fixture_path = fixture_path  # for tests/demo: read local HTML instead of the network

    def fetch(self) -> bytes:
        if self.fixture_path:
            with open(self.fixture_path, "rb") as f:
                return f.read()
        try:
            resp = requests.get(self.url, timeout=self.timeout_seconds, headers={
                "User-Agent": "Mozilla/5.0 (compatible; vessel-schedule-bot/1.0)"
            })
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            raise FetchError(f"Could not reach JNPA master report page: {e}") from e

    def parse(self, raw_content: bytes) -> ScrapeResult:
        soup = BeautifulSoup(raw_content, "lxml")

        # Report date: don't depend on CSS classes -- search visible text
        # for the phrase JNPA uses, since that's the part least likely to
        # change even through a template redesign.
        heading = soup.find(
            string=lambda s: bool(re.search(r"Daily Berthing Report as on", s, re.I)) and not isinstance(s, Comment)
        )
        report_date = None
        if heading:
            m = re.search(r"(\d{2})-(\d{2})-(\d{4})", heading)
            if m:
                d, mo, y = m.groups()
                report_date = datetime(int(y), int(mo), int(d)).date()
        if report_date is None:
            raise ParseError("Could not find 'Daily Berthing Report as on DD-MM-YYYY' heading on the page")

        table = soup.find("table")
        if table is None:
            raise ParseError("No <table> found on the master report page")

        body_rows = table.find("tbody").find_all("tr") if table.find("tbody") else table.find_all("tr")[1:]
        if not body_rows:
            raise ParseError("Master report table has a header but zero data rows")

        rows: list[ScrapedRow] = []
        discovered_links: dict[str, str] = {}
        terminals_seen: set[str] = set()
        current_terminal = None

        for tr in body_rows:
            cells = tr.find_all("td")
            if len(cells) < 7:
                continue
            texts = [c.get_text(strip=True) for c in cells]
            terminal, berth_no, via_no, vessel_name, cargo, berthed_on, expected_completion = texts[:7]

            if terminal:
                current_terminal = terminal
            terminal_code = current_terminal
            if terminal_code:
                # Every berth row counts as "we saw this terminal's section",
                # whether or not it currently has a vessel -- that's what
                # lets reconciliation later tell "confirmed empty" apart
                # from "this terminal's rows vanished from the page".
                terminals_seen.add(terminal_code)

            # Any report link in this row -> today's real URL for that terminal.
            link = cells[7].find("a") if len(cells) > 7 else None
            if link and link.get("href"):
                label = re.sub(r"\s+", " ", link.get_text(strip=True)).upper()
                mapped = LINK_TEXT_TO_TERMINAL.get(label)
                if mapped:
                    discovered_links[mapped] = urljoin(BASE_URL, link["href"])

            if not vessel_name:
                continue  # an empty berth -- nothing alongside right now

            fields = {
                "terminal_code": terminal_code,
                "berth_no": berth_no or None,
                "via_no": via_no or None,
                "vessel_name": vessel_name,
                "cargo_commodity": cargo or None,
                "berthed_on": _parse_dt(berthed_on.split(" ")[0], berthed_on.split(" ")[1] if " " in berthed_on else "") if berthed_on else None,
                "expected_completion": _parse_dt(expected_completion.split(" ")[0], expected_completion.split(" ")[1] if " " in expected_completion else "") if expected_completion else None,
            }
            rows.append(ScrapedRow(section="berthed", fields=fields, raw=dict(zip(
                ["terminal", "berth_no", "via_no", "vessel_name", "cargo", "berthed_on", "expected_completion"],
                texts[:7]))))

        return ScrapeResult(report_date=report_date, rows=rows, discovered_links=discovered_links,
                             terminals_seen=terminals_seen)

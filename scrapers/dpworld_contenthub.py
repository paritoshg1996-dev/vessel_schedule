"""
Shared discovery mechanism for every DP World terminal whose PDF isn't at
a stable URL -- so far MICT (Mundra, scrapers/mict.py) and CCT (Chennai,
scrapers/chennai_dpworld.py) both publish through the same Sitecore
Content Hub-backed GraphQL endpoint on dpworld.com, distinguished only by
which port/terminal a page's own CMS content names. Reverse-engineered
from MICT's berthing-report page's own JS bundle (search that bundle for
the literal string "get-assets" to find the query/variable shape again
if this ever needs re-deriving) -- see the original investigation in
scrapers/mict.py's git history for how the GraphQL query text and
variable names were found.

One HTTP round-trip (POST, to discover today's signed asset URL) plus a
second (GET, the actual PDF bytes) per scrape. No auth/cookies needed --
confirmed working from a plain unauthenticated `requests` call, the same
public API the page's own browser JS calls before rendering its document
list.
"""
from __future__ import annotations

import io
from typing import Optional

import pdfplumber
import requests

from scrapers.base import FetchError, ParseError, ScrapeResult, TerminalScraper

_GRAPHQL_QUERY = """
query GetDocuments(
  $categoryIds: [String!]
  $brandId: String!
  $portsAndTerminalsIds: [String!]
  $countryId: String
  $count: Int
  $endCursor: String
) {
  allM_Asset(
    where: {
      brandToAsset: { dP_Brands_ids: $brandId }
      documentCategoryToAsset: { dP_DocumentCategory_ids: $categoryIds }
      portsandTerminalsToAsset: { dP_PortsandTerminals_ids: $portsAndTerminalsIds }
      countryToAsset: { dP_Country_ids: $countryId }
    }
    orderBy: DOCUMENTDATE_DESC
    first: $count
    after: $endCursor
  ) {
    total
    pageInfo { hasNext endCursor }
    results { title documentDate urls documentisGated disclaimerText }
  }
}
"""
_USER_AGENT = "Mozilla/5.0 (compatible; vessel-schedule-bot/1.0)"


def discover_pdf_url(ports_and_terminals_id: str, source_label: str, timeout: int = 20) -> str:
    """POST the content-hub query filtered to one port/terminal id (e.g.
    "DP.PortsandTerminals.MundraMICT") and return the signed PDF URL from
    the single most recent result. `source_label` is just for error
    messages. Raises FetchError on any failure -- network, empty result
    set, or a result with no downloadable URL."""
    variables = {
        "categoryIds": ["DP.DocumentCategory.BerthingReport"],
        "brandId": "DP.Brands.DPWorld",
        "portsAndTerminalsIds": [ports_and_terminals_id],
        "countryId": "DP.Country.India",
        "count": 5,
        "endCursor": "",
    }
    headers = {"User-Agent": _USER_AGENT, "Content-Type": "application/json"}
    try:
        resp = requests.post(
            "https://www.dpworld.com/api/contenthub/get-assets",
            json={"query": _GRAPHQL_QUERY, "variables": variables},
            timeout=timeout, headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError) as e:
        raise FetchError(f"[{source_label}] could not discover the report URL: {e}") from e

    results = (data.get("allM_Asset") or {}).get("results") or []
    if not results:
        raise FetchError(f"[{source_label}] discovery call returned no documents (response: {data})")
    urls = results[0].get("urls") or {}
    if not urls:
        raise FetchError(f"[{source_label}] discovered document has no downloadable URL")
    return next(iter(urls.values()))["url"]


class DpWorldContentHubScraper(TerminalScraper):
    """Base for any DP World terminal discovered this way. Subclasses set
    `terminal_code` and `ports_and_terminals_id`, and implement
    `parse_words()` -- fetch()/parse() (single-page PDFs only, true of
    both MICT and CCT so far) live here once."""
    scope = "terminal"
    ports_and_terminals_id: str

    def __init__(self, url: str = None, fixture_path: str = None):
        # `url` is accepted for interface consistency with every other
        # scraper (run_pipeline.py always constructs `scraper_cls(url=url)`)
        # but unused -- there is no stable URL to pass; see module docstring.
        self.fixture_path = fixture_path

    def fetch(self) -> bytes:
        if self.fixture_path:
            with open(self.fixture_path, "rb") as f:
                return f.read()
        pdf_url = discover_pdf_url(self.ports_and_terminals_id, self.terminal_code,
                                    timeout=self.timeout_seconds)
        try:
            resp = requests.get(pdf_url, timeout=self.timeout_seconds, headers={"User-Agent": _USER_AGENT})
            resp.raise_for_status()
            return resp.content
        except requests.RequestException as e:
            raise FetchError(f"[{self.terminal_code}] could not fetch discovered PDF {pdf_url}: {e}") from e

    def parse(self, raw_content: bytes) -> ScrapeResult:
        try:
            pdf = pdfplumber.open(io.BytesIO(raw_content))
        except Exception as e:
            raise ParseError(f"[{self.terminal_code}] not a readable PDF: {e}") from e
        try:
            words = pdf.pages[0].extract_words()
            if not words:
                raise ParseError(f"[{self.terminal_code}] PDF had no extractable text (scanned image?)")
            return self.parse_words(words)
        finally:
            pdf.close()

    def parse_words(self, words: list[dict]) -> ScrapeResult:
        raise NotImplementedError

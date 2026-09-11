"""
Shared scraper interface + the PDF table-extraction engine.

Why coordinate snapping, not text order
----------------------------------------
Each terminal's "daily berthing report" PDF is a dense operational sheet --
tide tables, gate-movement counters, yard inventory, and three vessel
tables (expected / on berth / sailed) all laid out as side-by-side panels
on one landscape page, almost always exported from Excel.

Naive PDF-to-text extraction reads these in whatever order the PDF's
internal content stream happens to store them, which routinely is NOT
top-to-bottom/left-to-right. In samples pulled from JNPT's own terminal
reports, a vessel's name can land forty lines away from its own voyage
number and ETA in the extracted text, and an entire "vessels expected"
table can appear ABOVE the report's own title in the text stream. Regex
over that text will confidently produce wrong pairings.

The fix is to never trust stream order. `extract_words()` gives each word
its true (x0, top) position on the page -- that's real geometry, not
affected by however the content stream is ordered. `snap_table_by_headers`
below uses ONLY those coordinates: it finds the header row, turns each
header label into a column "lane" (an x-position), buckets every word
below it into rows by y-position, and assigns each word to its nearest
lane. That reconstructs the visual table regardless of stream order.

Every terminal parser in this package is a thin config (which header
labels to look for, how to map them to our canonical fields) on top of
this one engine -- that's the answer to "each terminal has a different
format": one robust engine, one small config per source.
"""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


class FetchError(Exception):
    """We couldn't retrieve the source at all: network down, timeout, non-200,
    site restructured its URLs. Transient by nature -- the right response is
    'try again next run, and tell someone if it keeps happening.'"""


class ParseError(Exception):
    """We got a response but couldn't make sense of it -- almost always
    because the source's layout changed. Not transient -- the right response
    is 'stop trusting this data and tell someone to look at the format.'"""


@dataclass
class ScrapedRow:
    section: str            # 'expected' | 'berthed' | 'sailed'
    fields: dict             # canonical field name -> value
    raw: dict                # original label -> original string (for staging)


@dataclass
class ScrapeResult:
    report_date: Optional[date]
    rows: list[ScrapedRow] = field(default_factory=list)
    # terminal_code -> freshly-discovered URL for that terminal's own report.
    # JNPT's PDF filenames change daily (e.g. "..._9_9_2026.pdf"), so the
    # master HTML page is also our way of finding *today's* real link
    # rather than trusting yesterday's filename.
    discovered_links: dict = field(default_factory=dict)
    # Terminal codes this run structurally saw a section for, whether or
    # not it had any vessel in it -- distinct from which terminals appear
    # in `rows`. A terminal with zero vessels but present in this set is
    # "confirmed empty" (safe to reconcile away old rows for); a terminal
    # ABSENT from this set entirely means we never saw its section this
    # run at all, which is just as consistent with a layout/schema change
    # silently dropping it as with anything else -- not safe to treat as
    # "confirmed empty". Defaults to the terminals in `rows` when a
    # scraper doesn't set this explicitly (single-terminal PDF scrapers
    # don't need to -- they only ever speak for their own terminal_code).
    terminals_seen: Optional[set] = None


class TerminalScraper(ABC):
    terminal_code: str
    scope: str = "terminal"       # 'terminal' | 'master'
    timeout_seconds: int = 20

    @abstractmethod
    def fetch(self) -> bytes:
        """Return the raw response body. Raise FetchError on failure."""

    @abstractmethod
    def parse(self, raw_content: bytes) -> ScrapeResult:
        """Turn raw bytes into rows. Raise ParseError on failure."""

    def run(self) -> ScrapeResult:
        raw = self.fetch()
        return self.parse(raw)


# ---------------------------------------------------------------------------
# Coordinate-snapping table engine (used by the PDF-based terminal scrapers)
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().upper())


def find_phrase_boxes(words: list[dict], phrase: str) -> list[dict]:
    """Find every occurrence of a (possibly multi-word) phrase in a word
    list and return its bounding box. Words must sit on the same line
    (within 4pt of vertical jitter) to count as one phrase match."""
    tokens = _norm(phrase).split(" ")
    norm_words = [_norm(w["text"]) for w in words]
    n = len(tokens)
    matches = []
    for i in range(len(words) - n + 1):
        if norm_words[i:i + n] != tokens:
            continue
        group = words[i:i + n]
        tops = [w["top"] for w in group]
        if max(tops) - min(tops) > 4:
            continue
        matches.append({
            "x0": min(w["x0"] for w in group),
            "x1": max(w["x1"] for w in group),
            "top": min(w["top"] for w in group),
            "bottom": max(w["bottom"] for w in group),
        })
    return matches


def snap_table_by_headers(
    words: list[dict],
    header_labels: list[str],
    top_after: Optional[float] = None,
    bottom_before_labels: Optional[list[str]] = None,
    row_tolerance: float = 3.0,
    min_filled: int = 2,
    header_margin: float = 1.0,
) -> list[dict]:
    """Reconstruct a table by column position rather than text order.

    1. Locate each header label -> its x-centre becomes a column "lane".
    2. Find the nearest occurrence of any `bottom_before_labels` phrase
       below the header, to know where this table ends (the next panel
       starts there).
    3. Bucket every word in between into rows by y-position (`top`,
       tolerant of `row_tolerance` points of jitter -- real PDFs are
       rarely pixel-perfect).
    4. Assign each word to its nearest lane by x-distance and join
       same-lane words left-to-right (handles multi-word values like a
       two-word vessel name).

    Returns a list of {header_label: value} dicts, top-to-bottom.
    Raises ParseError if fewer than half the requested headers are found
    at all -- that's the schema-drift signal a source has changed shape.

    `header_margin` (added after a live fetch of Adani's Mundra PDF)
    is the buffer added past the header row's own bottom (and subtracted
    before a `bottom_before` boundary) when deciding which words count as
    "data". The default of 1pt was fine for every JNPT report, whose
    header-to-first-row gap is comfortably larger than that -- but
    Adani's combined 4-terminal PDF has extremely tight line spacing
    (~3.7pt row height, with per-row jitter on individual header words),
    so a flat "+1" silently swallowed each panel's own row 1 into the
    excluded zone (its top landed *inside* header_bottom+1). Pass a
    smaller value (e.g. 0.1) for a source this tightly leaded; the
    default stays 1.0 so every existing caller is unaffected.
    """
    header_boxes = {}
    for label in header_labels:
        boxes = find_phrase_boxes(words, label)
        candidates = boxes if top_after is None else [b for b in boxes if b["top"] >= top_after]
        if candidates:
            header_boxes[label] = min(candidates, key=lambda b: b["top"])

    if len(header_boxes) < max(2, len(header_labels) // 2):
        found = list(header_boxes)
        raise ParseError(
            f"Expected header labels {header_labels}; only found {found}. "
            f"Source layout may have changed."
        )

    header_bottom = max(b["bottom"] for b in header_boxes.values())
    lanes = [(label, (b["x0"] + b["x1"]) / 2) for label, b in header_boxes.items()]

    bottom = None
    for label in (bottom_before_labels or []):
        tops = [b["top"] for b in find_phrase_boxes(words, label) if b["top"] > header_bottom + header_margin]
        if tops:
            cand = min(tops)
            bottom = cand if bottom is None else min(bottom, cand)

    data_words = [
        w for w in words
        if w["top"] > header_bottom + header_margin and (bottom is None or w["top"] < bottom - header_margin)
    ]
    data_words.sort(key=lambda w: w["top"])

    rows: list[list[dict]] = []
    current: list[dict] = []
    current_top: Optional[float] = None
    for w in data_words:
        if current_top is None or abs(w["top"] - current_top) <= row_tolerance:
            current.append(w)
            current_top = w["top"] if current_top is None else current_top
        else:
            rows.append(current)
            current = [w]
            current_top = w["top"]
    if current:
        rows.append(current)

    results = []
    for row_words in rows:
        row_words.sort(key=lambda w: w["x0"])
        lane_values = {label: [] for label, _ in lanes}
        for w in row_words:
            cx = (w["x0"] + w["x1"]) / 2
            nearest_label = min(lanes, key=lambda l: abs(l[1] - cx))[0]
            lane_values[nearest_label].append(w["text"])
        record = {label: " ".join(vals).strip() for label, vals in lane_values.items()}
        if sum(1 for v in record.values() if v) >= min_filled:
            record["_row_top"] = min(w["top"] for w in row_words)
            results.append(record)
    return results

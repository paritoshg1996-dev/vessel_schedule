import os
import sys

import pdfplumber

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.base import snap_table_by_headers, ParseError

PDF_PATH = os.path.join(os.path.dirname(__file__), "adversarial_sample.pdf")

EXPECTED = [
    {"VIA": "S1138", "VESSEL NAME": "OOCL MALAYSIA", "LOA": "366.47", "SERVICE": "CIX3", "LINE": "OCL"},
    {"VIA": "S1468", "VESSEL NAME": "BAI CHAY BRIDGE", "LOA": "266.65", "SERVICE": "JTI", "LINE": "ONE"},
    {"VIA": "S1481", "VESSEL NAME": "SEASPAN BRISBANE", "LOA": "260.00", "SERVICE": "CIX", "LINE": "EGI"},
    {"VIA": "S1408", "VESSEL NAME": "VANCOUVER EXPRESS", "LOA": "368.47", "SERVICE": "IOS", "LINE": "HLI"},
]


def test_snap_survives_scrambled_draw_order():
    with pdfplumber.open(PDF_PATH) as pdf:
        words = pdf.pages[0].extract_words()

    rows = snap_table_by_headers(
        words,
        header_labels=["VIA", "VESSEL NAME", "LOA", "SERVICE", "LINE"],
        bottom_before_labels=["SAILED VESSELS"],
    )

    assert len(rows) == len(EXPECTED), f"expected {len(EXPECTED)} rows, got {len(rows)}: {rows}"

    for got, want in zip(rows, EXPECTED):
        for key in want:
            assert got.get(key, "").strip() == want[key], (
                f"mismatch on {key}: got {got.get(key)!r} want {want[key]!r}\nfull row: {got}"
            )

    print("PASS -- all", len(rows), "rows reconstructed correctly despite scrambled draw order:")
    for r in rows:
        print(" ", r)


def test_stops_before_next_panel():
    with pdfplumber.open(PDF_PATH) as pdf:
        words = pdf.pages[0].extract_words()
    rows = snap_table_by_headers(
        words,
        header_labels=["VIA", "VESSEL NAME", "LOA", "SERVICE", "LINE"],
        bottom_before_labels=["SAILED VESSELS"],
    )
    joined = " ".join(str(r) for r in rows)
    assert "SHOULD NOT APPEAR" not in joined
    print("PASS -- did not bleed into the SAILED VESSELS panel below")


def test_schema_drift_detection():
    with pdfplumber.open(PDF_PATH) as pdf:
        words = pdf.pages[0].extract_words()
    try:
        snap_table_by_headers(words, header_labels=["TOTALLY", "DIFFERENT", "HEADERS", "NOT", "PRESENT"])
    except ParseError as e:
        print("PASS -- schema drift correctly raised ParseError:", e)
        return
    raise AssertionError("expected ParseError when headers are missing")


if __name__ == "__main__":
    test_snap_survives_scrambled_draw_order()
    test_stops_before_next_panel()
    test_schema_drift_detection()
    print("\nAll engine tests passed.")

"""
Builds a one-page PDF whose CONTENT STREAM writes cells in an order that
does not match the VISUAL row/column layout -- specifically mimicking what
we saw in JNPT's real terminal PDFs: the "Vessel Name" column is drawn as
a whole separate block, after and away from the "VIA / LOA / Service /
Line / ETA" block it visually lines up with.

If our extraction engine were reading text stream order (like a naive
`pdftotext` call), it would pair vessel names with the wrong voyage
numbers. Because it only trusts (x, y) position, it should reconstruct
the rows correctly regardless of draw order.
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4

OUT = "/home/claude/vessel-schedule/tests/adversarial_sample.pdf"

# Visual truth: 4 data rows, columns at fixed x-positions.
# (vessel name is visually the 2nd column, but we'll DRAW it last/out of order)
COLS = {"VIA": 60, "VESSEL NAME": 160, "LOA": 340, "SERVICE": 400, "LINE": 460}
ROWS_Y = [560, 540, 520, 500]  # top-down
DATA = [
    {"VIA": "S1138", "VESSEL NAME": "OOCL MALAYSIA", "LOA": "366.47", "SERVICE": "CIX3", "LINE": "OCL"},
    {"VIA": "S1468", "VESSEL NAME": "BAI CHAY BRIDGE", "LOA": "266.65", "SERVICE": "JTI", "LINE": "ONE"},
    {"VIA": "S1481", "VESSEL NAME": "SEASPAN BRISBANE", "LOA": "260.00", "SERVICE": "CIX", "LINE": "EGI"},
    {"VIA": "S1408", "VESSEL NAME": "VANCOUVER EXPRESS", "LOA": "368.47", "SERVICE": "IOS", "LINE": "HLI"},
]

c = canvas.Canvas(OUT, pagesize=landscape(A4))
c.setFont("Helvetica", 9)

# Header row, drawn normally, left to right
header_y = 590
for label, x in COLS.items():
    c.drawString(x, header_y, label)

# ADVERSARIAL draw order: everything except "VESSEL NAME" first, row by row...
for row, y in zip(DATA, ROWS_Y):
    for label in ["VIA", "LOA", "SERVICE", "LINE"]:
        c.drawString(COLS[label], y, row[label])

# ...then ALL vessel names afterwards, and even in reverse row order, and
# offset from where you'd expect a "next line" to be -- pure stream-order
# chaos. Visually they still land at (COLS["VESSEL NAME"], matching y).
for row, y in reversed(list(zip(DATA, ROWS_Y))):
    c.drawString(COLS["VESSEL NAME"], y, row["VESSEL NAME"])

# A second, unrelated panel below that a naive parser could bleed into --
# this is what "SAILED VESSELS" / "VESSELS ON BERTH" look like on the real
# reports. Our engine should stop before this using bottom_before_labels.
c.drawString(60, 460, "SAILED VESSELS")
c.drawString(60, 440, "S9999")
c.drawString(160, 440, "SHOULD NOT APPEAR")

c.save()
print("wrote", OUT)

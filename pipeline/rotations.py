"""
Turns the (shipping_line, service[, direction]) reference data in
ServiceRotation into "which ports does THIS voyage call at next" for any
given vessel_schedule row -- the actual thing a user wants to see,
computed rather than stored per-voyage (so updating one service's
rotation immediately applies to every current and future voyage on it,
with nothing to keep in sync).

A rotation is a cycle, not a line: the carrier's published list starts
wherever they happened to start writing it down, not necessarily at JNPT.
"Next ports" means everything after JNPT's position in that list, wrapping
around to the start, stopping just before JNPT comes around again --
i.e. the full remaining loop for this voyage before it's back here.

Directionality: some services run genuinely different port sets/orders
eastbound vs westbound (see models.ServiceRotation's docstring). JNPT's
own scrape doesn't currently say which leg a given voyage is on, so when
both directions exist for a (shipping_line, service), `rotation_summary`
returns both rather than guessing -- see its docstring for the shape.
"""
from models import ServiceRotation

# Whether to include confidence/source_url/notes in what gets exported
# downstream (Mongo, the API, the frontend). True while this data is
# still being built out and verified -- flip to False once the build is
# considered finalized, to show a clean "next ports" list without the
# research caveats attached. Nothing about the underlying data changes;
# this only controls what rotation_summary()/export payloads reveal.
EXPOSE_CONFIDENCE = True


def find_rotations(session, shipping_line: str, service: str) -> list["ServiceRotation"]:
    """All directions on record for this (shipping_line, service) -- 0, 1,
    or 2 rows (rarely more)."""
    if not shipping_line or not service:
        return []
    return (
        session.query(ServiceRotation)
        .filter_by(shipping_line=shipping_line.strip().upper(), service=service.strip().upper())
        .order_by(ServiceRotation.direction)
        .all()
    )


def next_ports(rotation: "ServiceRotation | None") -> list[dict]:
    """Ports after JNPT in `rotation`'s loop, in call order, wrapping once
    back to the start of the published list and stopping just before
    JNPT itself (that's arriving back here, not "next"). Returns []
    whenever there's nothing usable -- no rotation found, no fixed
    rotation to have (e.g. "ADHOC"), or JNPT's own position couldn't be
    matched in the published list."""
    if rotation is None or rotation.jnpt_index is None or not rotation.ports:
        return []
    ports = rotation.ports
    n = len(ports)
    return [ports[(rotation.jnpt_index + 1 + i) % n] for i in range(n - 1)]


def _leg_dict(rotation: "ServiceRotation") -> dict:
    d = {"direction": rotation.direction, "next_ports": next_ports(rotation)}
    if EXPOSE_CONFIDENCE:
        d["confidence"] = rotation.confidence
        d["source_url"] = rotation.source_url
        d["notes"] = rotation.notes
    return d


def rotation_summary(session, shipping_line: str, service: str) -> dict:
    """Describes what we know about this voyage's onward rotation --
    meant to be dropped straight into an API/export payload. Always
    returns a dict (never None) so callers don't need a None check.

    Shape:
      {"legs": [ {direction, next_ports, [confidence, source_url, notes]}, ... ]}

    `legs` has 0 entries (nothing on record for this line+service), 1
    (direction="single", or only one direction has been researched), or
    2 (both eastbound and westbound on record -- caller/UI decides how
    to present two candidate onward routes when the scrape itself can't
    say which leg this voyage is on).
    """
    rotations = find_rotations(session, shipping_line, service)
    return {"legs": [_leg_dict(r) for r in rotations]}

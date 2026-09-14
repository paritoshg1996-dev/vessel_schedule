"""
Turns the (shipping_line, service[, direction]) reference data in
ServiceRotation into "which ports does THIS voyage call at next" for any
given vessel_schedule row -- the actual thing a user wants to see,
computed rather than stored per-voyage (so updating one service's
rotation immediately applies to every current and future voyage on it,
with nothing to keep in sync).

A rotation is a cycle, not a line: the carrier's published list starts
wherever they happened to start writing it down, not necessarily at the
port a given voyage was scraped from. "Next ports" means everything
after THAT port's position in the list, wrapping around to the start,
stopping just before it comes around again -- i.e. the full remaining
loop for this voyage before it's back at the port it was scraped from.

FROM_PORT: since this now covers 4 ports (JNPT, Mundra, Cochin, Chennai),
every call has to say which one the voyage was actually observed at --
see pipeline/ports.py's module docstring for why a single JNPT-only
anchor couldn't work once a rotation could plausibly touch more than one
of our 4 ports (confirmed common in practice: MSC/IAS calls both Nhava
Sheva and Mundra; MSC/MALABAR calls Cochin and Mundra; HMM's FIM calls
Nhava Sheva, Mundra AND Kattupalli in one loop). `from_port` must be one
of "JNPT"/"MUNDRA"/"COCHIN"/"CHENNAI" -- pass whichever port_code the
vessel_schedule row this rotation is being looked up for actually has.

Directionality: some services run genuinely different port sets/orders
eastbound vs westbound (see models.ServiceRotation's docstring). The
scrape doesn't currently say which leg a given voyage is on, so when
both directions exist for a (shipping_line, service), `rotation_summary`
returns both rather than guessing -- see its docstring for the shape.
"""
from models import ServiceRotation
from pipeline.ports import find_port_index

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


def next_ports(rotation: "ServiceRotation | None", from_port: str) -> list[dict]:
    """Ports after `from_port` in `rotation`'s loop, in call order,
    wrapping once back to the start of the published list and stopping
    just before `from_port` itself (that's arriving back there, not
    "next"). `from_port` is one of "JNPT"/"MUNDRA"/"COCHIN"/"CHENNAI" --
    the port THIS voyage was actually scraped at, not necessarily JNPT
    (see module docstring). Returns [] whenever there's nothing usable --
    no rotation found, no fixed rotation to have (e.g. "ADHOC"), or
    `from_port` doesn't appear anywhere in the published list (a real,
    non-error case: plenty of rotations touch only one of our 4 ports)."""
    if rotation is None or not rotation.ports:
        return []
    index = find_port_index(rotation.ports, from_port)
    if index is None:
        return []
    ports = rotation.ports
    n = len(ports)
    return [ports[(index + 1 + i) % n] for i in range(n - 1)]


def _leg_dict(rotation: "ServiceRotation", from_port: str) -> dict:
    d = {"direction": rotation.direction, "next_ports": next_ports(rotation, from_port)}
    if EXPOSE_CONFIDENCE:
        d["confidence"] = rotation.confidence
        d["source_url"] = rotation.source_url
        d["notes"] = rotation.notes
    return d


def rotation_summary(session, shipping_line: str, service: str, from_port: str) -> dict:
    """Describes what we know about this voyage's onward rotation --
    meant to be dropped straight into an API/export payload. Always
    returns a dict (never None) so callers don't need a None check.

    `from_port` must be one of "JNPT"/"MUNDRA"/"COCHIN"/"CHENNAI" -- the
    port this specific vessel_schedule row was scraped at (its
    port_code). Required, not defaulted: guessing JNPT for a Mundra/
    Cochin/Chennai row would silently anchor on the wrong position (or
    the wrong port entirely) in any rotation touching more than one of
    our ports -- exactly the bug this function used to have.

    Shape:
      {"legs": [ {direction, next_ports, [confidence, source_url, notes]}, ... ]}

    `legs` has 0 entries (nothing on record for this line+service), 1
    (direction="single", or only one direction has been researched), or
    2 (both eastbound and westbound on record -- caller/UI decides how
    to present two candidate onward routes when the scrape itself can't
    say which leg this voyage is on).
    """
    rotations = find_rotations(session, shipping_line, service)
    return {"legs": [_leg_dict(r, from_port) for r in rotations]}

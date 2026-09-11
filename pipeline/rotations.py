"""
Turns the (shipping_line, service) reference data in ServiceRotation into
"which ports does THIS voyage call at next" for any given vessel_schedule
row -- the actual thing a user wants to see, computed rather than stored
per-voyage (so updating one service's rotation immediately applies to
every current and future voyage on it, with nothing to keep in sync).

A rotation is a cycle, not a line: the carrier's published list starts
wherever they happened to start writing it down, not necessarily at JNPT.
"Next ports" means everything after JNPT's position in that list, wrapping
around to the start, stopping just before JNPT comes around again --
i.e. the full remaining loop for this voyage before it's back here.
"""
from models import ServiceRotation


def find_rotation(session, shipping_line: str, service: str) -> "ServiceRotation | None":
    if not shipping_line or not service:
        return None
    return (
        session.query(ServiceRotation)
        .filter_by(shipping_line=shipping_line.strip().upper(), service=service.strip().upper())
        .one_or_none()
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


def rotation_summary(session, shipping_line: str, service: str) -> dict:
    """One dict describing what we know about this voyage's onward
    rotation -- meant to be dropped straight into an API/export payload.
    Always returns a dict (never None) so callers don't need a None
    check; `confidence` tells you whether `next_ports` is meaningful."""
    rotation = find_rotation(session, shipping_line, service)
    if rotation is None:
        return {"confidence": "unresolved", "next_ports": [], "source_url": None, "notes": None}
    return {
        "confidence": rotation.confidence,
        "next_ports": next_ports(rotation),
        "source_url": rotation.source_url,
        "notes": rotation.notes,
    }

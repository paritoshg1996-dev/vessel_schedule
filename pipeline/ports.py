"""
Canonical port identity, shared by anything that needs to recognize "is
this port-name string one of our 4 tracked ports" or "are these two
port-name strings the same physical port."

Two distinct concerns live here on purpose:

1. HOME_PORT_ALIASES / find_port_index(): name variants for the 4 ports
   this pipeline actually scrapes (JNPT, Mundra, Cochin, Chennai) -- used
   to find "where is THIS port in a carrier's published rotation" so
   next_ports() (see pipeline/rotations.py) can anchor on the right
   position for whichever port a vessel actually called at. Before this
   module existed, that anchor was a single `jnpt_index` column computed
   once at seed time against JNPT-only aliases -- which meant it was
   wrong (either empty or anchored on the wrong port) for any rotation
   touching more than one of our 4 ports, which turned out to be the
   common case once Mundra/Cochin/Chennai were added (e.g. MSC/IAS calls
   both Nhava Sheva and Mundra; MSC/MALABAR calls Cochin and Mundra; HMM's
   FIM calls Nhava Sheva, Mundra AND Kattupalli in the same loop).
   Computing the anchor dynamically, given which port to anchor on,
   fixes this without needing per-port stored columns.

2. normalize_port_name(): general spelling-variant collapsing for ANY
   port name (including ones we don't track ourselves) -- used when
   comparing two port-name strings for equality, so research data
   entered with a different but equivalent spelling doesn't silently
   fail to match (e.g. this pipeline's own research data has both "Port
   Klang" and "Port Kelang" for the same Malaysian port, and both
   "Khor Fakkan" and "Khorfakkan").

Kattupalli is deliberately NOT aliased to Chennai (or vice versa) even
though they're geographically close and often grouped colloquially --
they're different physical terminals, and conflating them would be
exactly the kind of unearned guess this project has otherwise avoided
(see research/service_rotations_2026_09.py's own docstring on that
discipline). Same reasoning for keeping Mundra's own name un-aliased to
anything else.

This is NOT a full UN/LOCODE resolution engine -- just enough evidence-
based alias/spelling collapsing to stop known duplicates in our own data
from looking like different ports. A proper canonical port list (e.g.
cross-referencing container_traffic's own unlocode.xlsx) is a further
improvement, not a prerequisite for this module to be correct.
"""

# Name variants seen in real rotation research data or plausible as
# scraped/typed input, for the 4 ports this pipeline tracks. Matched
# after normalize_port_name()'s lowercase/whitespace cleanup, so this
# only needs to list genuinely different WORDS, not spacing/case
# variants of the same one.
HOME_PORT_ALIASES: dict[str, set[str]] = {
    "JNPT": {"nhava sheva", "jnpt", "jnpa", "jawaharlal nehru port", "jawaharlal nehru"},
    "MUNDRA": {"mundra", "mundra port"},
    "COCHIN": {"cochin", "kochi", "vallarpadam", "cochin port"},
    "CHENNAI": {"chennai", "chennai port", "madras"},
}

# Known equivalent spellings hit during research for ports we DON'T
# track ourselves but that show up as legs of a rotation -- collapsing
# these means two spellings of the same physical port are recognized as
# equal when comparing port-name strings, without hand-editing every
# existing research entry to agree on one spelling. Deliberately a
# short, evidence-based list (each entry earned by an actual collision
# found in this pipeline's own data), not a general transliteration
# engine -- add to it as new variants turn up.
_SPELLING_VARIANTS: dict[str, str] = {
    "port kelang": "port klang",
    "khorfakkan": "khor fakkan",
    "ad dammam": "dammam",
}


def normalize_port_name(name: str | None) -> str:
    """Lowercase, whitespace-collapsed, and known-variant-collapsed --
    the canonical form two port-name strings should be compared in.
    Empty string (never None) for missing input, so callers can compare
    directly without a None check."""
    if not name:
        return ""
    n = " ".join(name.strip().lower().split())
    return _SPELLING_VARIANTS.get(n, n)


def find_port_index(ports: list[dict], home_port_code: str) -> "int | None":
    """Index in `ports` (a ServiceRotation.ports-shaped list of
    {"port": str, ...} dicts) whose name matches `home_port_code` (one
    of "JNPT"/"MUNDRA"/"COCHIN"/"CHENNAI") -- or None if that port
    doesn't appear in this rotation at all, or `home_port_code` isn't
    one of the 4 we track. First match wins, matching this pipeline's
    existing convention (a rotation calling the same home port twice in
    one loop is rare and not specially handled here)."""
    aliases = HOME_PORT_ALIASES.get((home_port_code or "").strip().upper())
    if not aliases:
        return None
    for i, p in enumerate(ports or []):
        if normalize_port_name(p.get("port")) in aliases:
            return i
    return None

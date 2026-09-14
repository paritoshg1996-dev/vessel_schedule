import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ServiceRotation, get_engine, get_session, init_db
from pipeline.ports import find_port_index, normalize_port_name
from pipeline.rotations import next_ports, rotation_summary


def fresh_session():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    return get_session(engine)


def port(name, country="India"):
    return {"port": name, "country": country}


class FakeRotation:
    """Minimal stand-in for a ServiceRotation row -- just the attributes
    next_ports()/_leg_dict() actually read. Avoids a DB round-trip for
    the pure port-arithmetic tests below."""
    def __init__(self, ports, direction="single", confidence="verified",
                 source_url=None, notes=None):
        self.ports = ports
        self.direction = direction
        self.confidence = confidence
        self.source_url = source_url
        self.notes = notes


def test_normalize_port_name_collapses_known_variants():
    assert normalize_port_name("Port Klang") == normalize_port_name("Port Kelang")
    assert normalize_port_name("Khor Fakkan") == normalize_port_name("Khorfakkan")
    assert normalize_port_name("Dammam") == normalize_port_name("Ad Dammam")
    assert normalize_port_name("  Mundra  ") == "mundra"
    assert normalize_port_name(None) == ""
    # unrelated names must NOT collapse into each other
    assert normalize_port_name("Mundra") != normalize_port_name("Cochin")
    print("PASS -- normalize_port_name collapses known spelling variants, nothing else")


def test_find_port_index_finds_all_home_port_aliases():
    ports = [port("Jebel Ali", "UAE"), port("Nhava Sheva"), port("Mundra"),
             port("Colombo", "Sri Lanka")]
    assert find_port_index(ports, "JNPT") == 1
    assert find_port_index(ports, "MUNDRA") == 2
    # case/whitespace-insensitive, and alternate spellings of the same port
    assert find_port_index([port("  JAWAHARLAL NEHRU  ")], "JNPT") == 0
    assert find_port_index([port("Kochi")], "COCHIN") == 0
    assert find_port_index([port("Chennai Port")], "CHENNAI") == 0
    print("PASS -- find_port_index resolves every home-port alias, not just the canonical name")


def test_find_port_index_none_when_port_absent_or_code_unknown():
    ports = [port("Cochin"), port("Mundra"), port("Karachi", "Pakistan")]
    assert find_port_index(ports, "JNPT") is None          # genuinely never calls JNPT
    assert find_port_index(ports, "CHENNAI") is None        # genuinely never calls Chennai
    assert find_port_index(ports, "NOT_A_TRACKED_PORT") is None  # unknown code, not an error
    assert find_port_index([], "MUNDRA") is None
    print("PASS -- find_port_index returns None (not an error) when the port genuinely isn't there")


def test_next_ports_anchors_on_the_actual_port_not_always_jnpt():
    """The regression test for the bug this module fixes: a rotation
    touching both JNPT and Mundra at different positions must give a
    DIFFERENT, each-correct answer depending on which port the voyage
    was actually scraped at -- not silently reuse a JNPT-only anchor."""
    # Shaped like a real one from this pass: MSC/IAS --
    # Jebel Ali - Khalifa - Sohar - Nhava Sheva - Mundra - Ngqura - ... - Jebel Ali
    rotation = FakeRotation([
        port("Jebel Ali", "UAE"), port("Khalifa", "UAE"), port("Sohar", "Oman"),
        port("Nhava Sheva"), port("Mundra"), port("Ngqura", "South Africa"),
        port("Abidjan", "Ivory Coast"),
    ])

    from_jnpt = next_ports(rotation, "JNPT")
    from_mundra = next_ports(rotation, "MUNDRA")

    assert [p["port"] for p in from_jnpt] == [
        "Mundra", "Ngqura", "Abidjan", "Jebel Ali", "Khalifa", "Sohar",
    ], from_jnpt
    assert [p["port"] for p in from_mundra] == [
        "Ngqura", "Abidjan", "Jebel Ali", "Khalifa", "Sohar", "Nhava Sheva",
    ], from_mundra
    assert from_jnpt != from_mundra
    print("PASS -- next_ports anchors on JNPT vs Mundra differently, both correctly")


def test_next_ports_empty_when_rotation_never_touches_from_port():
    """Shaped like MSC/MALABAR: Cochin and Mundra, but never Nhava Sheva.
    A JNPT-side lookup must come back empty, not wrong or an error --
    this is the common case that used to silently break before this fix
    (rotation.jnpt_index was simply None for any non-JNPT-touching loop,
    which happened to be correct here by accident, but for the wrong
    reason -- and broke as soon as the SAME rotation was looked up from
    Mundra or Cochin instead, which is what this test's second half
    covers)."""
    rotation = FakeRotation([
        port("Cochin"), port("Mundra"), port("Karachi", "Pakistan"),
        port("Jebel Ali", "UAE"), port("Colombo", "Sri Lanka"),
    ])
    assert next_ports(rotation, "JNPT") == []
    assert next_ports(rotation, "CHENNAI") == []
    # but Cochin and Mundra -- the ports this rotation actually calls --
    # must each resolve to a real, different answer
    assert [p["port"] for p in next_ports(rotation, "COCHIN")] == [
        "Mundra", "Karachi", "Jebel Ali", "Colombo",
    ]
    assert [p["port"] for p in next_ports(rotation, "MUNDRA")] == [
        "Karachi", "Jebel Ali", "Colombo", "Cochin",
    ]
    print("PASS -- next_ports is empty for a port the rotation never calls, correct for ones it does")


def test_next_ports_none_rotation_or_no_fixed_rotation():
    assert next_ports(None, "JNPT") == []
    assert next_ports(FakeRotation([], confidence="no_fixed_rotation"), "JNPT") == []
    print("PASS -- next_ports handles no-rotation-on-record and no_fixed_rotation without erroring")


def test_rotation_summary_requires_from_port_and_reflects_it():
    """End-to-end through a real DB row (matching how seed_service_rotations.py
    actually writes one), covering the two-directions-on-record shape too."""
    session = fresh_session()
    session.add(ServiceRotation(
        shipping_line="CCA", service="BIGEX", direction="eastbound",
        ports=[port("Fujairah", "UAE"), port("Nhava Sheva"), port("Mundra")],
        jnpt_index=1, confidence="needs_verification", source_url="https://example.com", notes="test",
    ))
    session.add(ServiceRotation(
        shipping_line="CCA", service="BIGEX", direction="westbound",
        ports=[port("Nhava Sheva"), port("Mundra"), port("Fujairah", "UAE")],
        jnpt_index=0, confidence="needs_verification", source_url="https://example.com", notes="test",
    ))
    session.commit()

    summary_from_jnpt = rotation_summary(session, "CCA", "BIGEX", "JNPT")
    summary_from_mundra = rotation_summary(session, "CCA", "BIGEX", "MUNDRA")

    assert len(summary_from_jnpt["legs"]) == 2, summary_from_jnpt
    eastbound = next(l for l in summary_from_jnpt["legs"] if l["direction"] == "eastbound")
    # eastbound ports = [Fujairah, Nhava Sheva, Mundra] -- anchored on JNPT
    # (index 1), wrapping: Mundra, then back around to Fujairah.
    assert [p["port"] for p in eastbound["next_ports"]] == ["Mundra", "Fujairah"]
    eastbound_from_mundra = next(l for l in summary_from_mundra["legs"] if l["direction"] == "eastbound")
    # same leg, anchored on Mundra (index 2) instead -- a different,
    # equally correct wraparound order, not the same list reused.
    assert [p["port"] for p in eastbound_from_mundra["next_ports"]] == ["Fujairah", "Nhava Sheva"]
    assert eastbound["confidence"] == "needs_verification"  # EXPOSE_CONFIDENCE fields present
    print("PASS -- rotation_summary threads from_port through every leg correctly")


def test_rotation_summary_empty_when_nothing_on_record():
    session = fresh_session()
    summary = rotation_summary(session, "ZZZ", "NOT_A_REAL_SERVICE", "JNPT")
    assert summary == {"legs": []}
    print("PASS -- rotation_summary returns an empty-legs dict, never None, for an unknown combo")


if __name__ == "__main__":
    test_normalize_port_name_collapses_known_variants()
    test_find_port_index_finds_all_home_port_aliases()
    test_find_port_index_none_when_port_absent_or_code_unknown()
    test_next_ports_anchors_on_the_actual_port_not_always_jnpt()
    test_next_ports_empty_when_rotation_never_touches_from_port()
    test_next_ports_none_rotation_or_no_fixed_rotation()
    test_rotation_summary_requires_from_port_and_reflects_it()
    test_rotation_summary_empty_when_nothing_on_record()
    print("\nAll rotation/port-matching tests passed.")

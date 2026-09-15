import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ServiceRotation, VesselSchedule, get_engine, get_session, init_db
from pipeline.mongo_export import _rotation_fields, _vessel_schedule_doc

TODAY = date(2026, 9, 15)


def fresh_session():
    engine = get_engine("sqlite:///:memory:")
    init_db(engine)
    return get_session(engine)


def port(name, country="India"):
    return {"port": name, "country": country}


def test_rotation_fields_merges_both_directions_normalized_and_deduped():
    session = fresh_session()
    # Same shape as CCA/BIGEX: two directions, overlapping ports, plus a
    # known spelling variant ("Port Kelang") that should collapse with
    # the canonical form used elsewhere.
    session.add(ServiceRotation(
        shipping_line="CCA", service="BIGEX", direction="eastbound",
        ports=[port("Fujairah", "UAE"), port("Nhava Sheva"), port("Port Kelang", "Malaysia")],
        confidence="needs_verification", source_url="https://example.com", notes="t",
    ))
    session.add(ServiceRotation(
        shipping_line="CCA", service="BIGEX", direction="westbound",
        ports=[port("Nhava Sheva"), port("Port Klang", "Malaysia"), port("Fujairah", "UAE")],
        confidence="needs_verification", source_url="https://example.com", notes="t",
    ))
    session.commit()

    fields = _rotation_fields(session, "CCA", "BIGEX", "JNPT")

    assert len(fields["rotation"]["legs"]) == 2
    # "Port Kelang" and "Port Klang" must collapse to one entry, not two
    assert fields["next_ports_normalized"] == sorted({"fujairah", "port klang"})
    print("PASS -- next_ports_normalized merges both legs and collapses known spelling variants")


def test_rotation_fields_empty_when_nothing_on_record():
    session = fresh_session()
    fields = _rotation_fields(session, "ZZZ", "NOT_REAL", "MUNDRA")
    assert fields == {"rotation": {"legs": []}, "next_ports_normalized": []}
    print("PASS -- an uncovered (line, service) exports as empty, not an error or a guess")


def test_vessel_schedule_doc_uses_the_row_own_port_code_as_anchor():
    """The actual regression this wiring exists for: a vessel scraped at
    Mundra must get Mundra-anchored next_ports, not JNPT-anchored ones,
    purely from its own port_code -- no caller has to remember to pass
    the right thing separately."""
    session = fresh_session()
    session.add(ServiceRotation(
        shipping_line="MSC", service="IAS", direction="single",
        ports=[port("Jebel Ali", "UAE"), port("Nhava Sheva"), port("Mundra"),
               port("Ngqura", "South Africa")],
        confidence="needs_verification", source_url=None, notes=None,
    ))
    v = VesselSchedule(
        port_code="MUNDRA", terminal_code="AMCT", status="expected",
        vessel_name="TEST VESSEL", via_no="V1", service="IAS", shipping_line="MSC",
        report_date=TODAY,
    )
    session.add(v)
    session.commit()

    doc = _vessel_schedule_doc(session, v)
    # Anchored on Mundra (index 2): wraps Ngqura, Jebel Ali, Nhava Sheva --
    # a JNPT anchor would have wrongly produced ["mundra", "ngqura", "jebel ali"] instead.
    assert doc["next_ports_normalized"] == sorted(["ngqura", "jebel ali", "nhava sheva"])
    print("PASS -- _vessel_schedule_doc anchors on the row's own port_code automatically")


if __name__ == "__main__":
    test_rotation_fields_merges_both_directions_normalized_and_deduped()
    test_rotation_fields_empty_when_nothing_on_record()
    test_vessel_schedule_doc_uses_the_row_own_port_code_as_anchor()
    print("\nAll mongo_export rotation-field tests passed.")

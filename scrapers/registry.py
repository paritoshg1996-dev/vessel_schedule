"""
The list of sources the pipeline pulls. Adding a new terminal or an
entirely new port is meant to mean: add one row here + one small scraper
module, not touch the pipeline, DB, alerting, or frontend code.
"""

TERMINALS = [
    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="JNPT_MASTER", terminal_name="JNPA Daily Berthing Report (all terminals)",
         operator="JNPA", cargo_type="mixed", source_type="html",
         source_url="https://www.jnport.gov.in/page/daily-berthing-report/M2VlS0pwUXZ3akhSV0E0RDFUVlhxQT09",
         is_container_terminal=False),

    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="NSFT", terminal_name="Nhava Sheva Freeport Terminal",
         operator="NSFT", cargo_type="container", source_type="pdf",
         source_url="https://www.jnport.gov.in/uploads/berthing_report/pdf/15/Daily_Berthing_Report_9_9_2026.pdf",
         is_container_terminal=True),

    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="NSICT", terminal_name="Nhava Sheva International Container Terminal",
         operator="DP World", cargo_type="container", source_type="pdf",
         source_url="https://www.jnport.gov.in/uploads/berthing_report/pdf/13/BERTHING_CT.pdf",
         is_container_terminal=True),

    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="NSIGT", terminal_name="Nhava Sheva India Gateway Terminal",
         operator="DP World", cargo_type="container", source_type="pdf",
         source_url="https://www.jnport.gov.in/uploads/berthing_report/pdf/14/BERTHING_GT.pdf",
         is_container_terminal=True),

    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="APMT", terminal_name="APM Terminals Mumbai (GTI)",
         operator="APM Terminals", cargo_type="container", source_type="pdf",
         source_url="https://www.jnport.gov.in/uploads/berthing_report/pdf/16/APMT_Berthing_Report_-_09-Sep-2026.pdf",
         is_container_terminal=True),

    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="BMCT", terminal_name="Bharat Mumbai Container Terminal",
         operator="PSA International", cargo_type="container", source_type="pdf",
         source_url="https://www.jnport.gov.in/uploads/berthing_report/pdf/17/Berthing_Sheet_09_SEP_2026.pdf",
         is_container_terminal=True),

    # Non-container JNPT terminals -- kept in the registry (and the DB) for
    # completeness since they're on the same master page, but filtered out
    # of the "container ships" views by is_container_terminal=False.
    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="BPCL", terminal_name="BPCL Liquid Terminal",
         operator="BPCL", cargo_type="liquid", source_type="pdf",
         source_url="https://www.jnport.gov.in/uploads/berthing_report/pdf/18/Daily_Report_09_Sep_26.pdf",
         is_container_terminal=False),
    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="JJLT", terminal_name="JJLT Liquid Terminal",
         operator="JJLT", cargo_type="liquid", source_type="pdf",
         source_url="https://www.jnport.gov.in/uploads/berthing_report/pdf/21/Berth_Plan_2026-09-09.pdf",
         is_container_terminal=False),
    dict(port_code="JNPT", port_name="Jawaharlal Nehru Port",
         terminal_code="NSDT", terminal_name="Nhava Sheva Dry Bulk Terminal",
         operator="NSDT", cargo_type="dry_bulk", source_type="pdf",
         source_url="https://www.jnport.gov.in/uploads/berthing_report/pdf/19/Bulk_Terminal_Daily_Report_SEPT__09_09_2026.pdf",
         is_container_terminal=False),
]

CONTAINER_TERMINAL_CODES = [t["terminal_code"] for t in TERMINALS if t["is_container_terminal"]]

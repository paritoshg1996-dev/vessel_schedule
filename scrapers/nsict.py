from scrapers.dpworld_common import DpWorldTerminalScraper


class NsictScraper(DpWorldTerminalScraper):
    terminal_code = "NSICT"

    def __init__(self, url: str = None, fixture_path: str = None):
        super().__init__(
            url or "https://www.jnport.gov.in/uploads/berthing_report/pdf/13/BERTHING_CT.pdf",
            fixture_path,
        )

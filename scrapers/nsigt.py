from scrapers.dpworld_common import DpWorldTerminalScraper


class NsigtScraper(DpWorldTerminalScraper):
    terminal_code = "NSIGT"

    def __init__(self, url: str = None, fixture_path: str = None):
        super().__init__(
            url or "https://www.jnport.gov.in/uploads/berthing_report/pdf/14/BERTHING_GT.pdf",
            fixture_path,
        )

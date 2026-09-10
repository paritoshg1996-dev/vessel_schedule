from scrapers.jnpa_master import JnpaMasterScraper
from scrapers.apmt import ApmtScraper
from scrapers.nsict import NsictScraper
from scrapers.nsigt import NsigtScraper
from scrapers.bmct import BmctScraper
from scrapers.nsft import NsftScraper

SCRAPER_CLASSES = {
    "JNPT_MASTER": JnpaMasterScraper,
    "APMT": ApmtScraper,
    "NSICT": NsictScraper,
    "NSIGT": NsigtScraper,
    "BMCT": BmctScraper,
    "NSFT": NsftScraper,
    # BPCL / JJLT / NSDT are non-container terminals -- registered in
    # registry.py for completeness but no PDF parser is implemented for
    # them yet since the container schedule doesn't need their data.
}

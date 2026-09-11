from scrapers.jnpa_master import JnpaMasterScraper
from scrapers.apmt import ApmtScraper
from scrapers.nsict import NsictScraper
from scrapers.nsigt import NsigtScraper
from scrapers.bmct import BmctScraper
from scrapers.nsft import NsftScraper
from scrapers.mundra_adani import AdaniMundraScraper
from scrapers.mict import MictScraper

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

    # Mundra Port. "MUNDRA_ADANI" is a dispatch key covering all four of
    # Adani's own terminals in one fetch (AMCT/T2/AICTPL/ACMTPL never
    # appear as SCRAPER_CLASSES keys themselves) -- same role
    # "JNPT_MASTER" plays above. MICT is DP World's separate terminal,
    # its own single fetch.
    "MUNDRA_ADANI": AdaniMundraScraper,
    "MICT": MictScraper,
}

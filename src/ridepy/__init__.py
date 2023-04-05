from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    pass

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = logging.StreamHandler()
handler.setLevel(logging.WARNING)
logger.addHandler(handler)

__author__ = "Felix Jung and Debsankha Manik"
__email__ = "felix.jung@tu-dresden.de; dmanik@debsankha.net"

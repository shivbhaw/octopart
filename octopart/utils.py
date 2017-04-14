from collections import OrderedDict
import logging
import sys

import backoff
from requests.exceptions import RequestException

from octopart.exceptions import OctopartError

logger = logging.getLogger(__name__)


def _raise_octopart_error(info):
    exc_type, error, _ = sys.exc_info()
    logger.warning('Octopart client error: %s', error.message)
    raise OctopartError(str(exc_type))


exponential_backoff = backoff.on_exception(
    backoff.expo,
    RequestException,
    max_tries=5,
    on_giveup=_raise_octopart_error)


def chunked(list_, chunksize=20):
    """
    Partitions list into chunks of a given size.

    NOTE: Octopart enforces that its 'parts/match' endpoint take no more
    than 20 queries in a single request.

    Args:
        list_ (list): list to be partitioned
        chunksize (int): size of resulting chunks

    Returns:
        list of lists.
    """
    chunks = []
    for i in range(0, len(list_), chunksize):
        chunks.append(list_[i:i + chunksize])
    return chunks


def unique(list_):
    """
    Removes duplicate entries from list, keeping it in its original order.
    """
    return list(OrderedDict.fromkeys(list_))

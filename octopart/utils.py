from collections import OrderedDict
import logging
import sys

import backoff
from requests.exceptions import RequestException

from octopart.exceptions import OctopartError

logger = logging.getLogger(__name__)


def _raise_octopart_error(info):
    error = sys.exc_info()[1]
    raise OctopartError(error.message)


exponential_backoff = backoff.on_exception(
    backoff.expo,
    RequestException,
    max_tries=5,
    on_giveup=_raise_octopart_error)


def chunked(_list, chunksize=20):
    """
    Partitions list into chunks of a given size.

    NOTE: Octopart enforces that its 'parts/match' endpoint take no more
    than 20 queries in a single request.

    Args:
        _list (list): list to be partitioned
        chunksize (int): size of resulting chunks

    Returns:
        list of lists.
    """
    chunks = []
    for i in range(0, len(_list), chunksize):
        chunks.append(_list[i:i + chunksize])
    return chunks


def unique(_list):
    """
    Removes duplicate entries from list, keeping it in the original order.
    """
    return list(OrderedDict.fromkeys(_list))

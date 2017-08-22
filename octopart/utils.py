import collections
import itertools
import json
import logging
from typing import List
from urllib.parse import urlencode


logger = logging.getLogger(__name__)


URL_MAX_LENGTH = 8000


def chunked(list_: List, chunksize: int=20) -> List[List]:
    """
    Partitions list into chunks of a given size.

    NOTE: Octopart enforces that its 'parts/match' endpoint take no more
    than 20 queries in a single request.

    Args:
        list_: list to be partitioned
        chunksize: size of resulting chunks

    Returns:
        list of lists.
    """
    chunks: List[List] = []
    for i in range(0, len(list_), chunksize):
        chunks.append(list_[i:i + chunksize])
    return chunks


def chunk_queries(queries: List) -> List[List]:
    """
    Partitions list into chunks, and ensures that each chunk is small enough
    to not trigger an HTTP 414 error (Request URI Too Large).

    Args:
        queries (list)

    Returns:
        list
    """
    chunks: List[List] = []
    # Octopart can only handle 20 queries per request, so split into chunks.
    for chunk in chunked(queries):
        chunks.extend(split_chunk(chunk))
    return chunks


def split_chunk(chunk: List) -> List[List]:
    """
    Split chunk into smaller pieces if encoding the chunk into a URL would
    result in an HTTP 414 error.

    Args:
        chunk (list)

    Returns:
        list of chunks
    """
    encoded = urlencode({'queries': json.dumps(chunk)})
    if len(encoded) > URL_MAX_LENGTH:
        # Split chunk in half to avoid HTTP 414 error.
        mid = len(chunk) // 2
        left, right = chunk[:mid], chunk[mid:]
        # Recurse in case either half is still too long.
        return flatten([split_chunk(left), split_chunk(right)])
    else:
        return [chunk]


def flatten(list_of_lists: List[List]) -> List:
    """Chain together a list of lists

    >>> flatten([1, 2], [3, 4, 5], ['a'])
    [1, 2, 3, 4, 5, 'a']
    """
    return list(itertools.chain(*list_of_lists))


def unique(list_: List) -> List:
    """Remove duplicate entries from list, keeping it in its original order

    >>> unique([1, 2, 2, 3, 4, 6, 2, 5])
    [1, 2, 3, 4, 6, 5]

    >>> unique(['bb', 'aa', 'aa', 'aa', 'aa', 'aa', 'bb'])
    ['bb', 'aa']
    """
    return list(collections.OrderedDict.fromkeys(list_))

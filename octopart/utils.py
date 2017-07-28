import collections
import itertools
import json
import logging
from typing import List
from urllib.parse import urlencode


from .directives import IncludeDirectives


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
    return list(itertools.chain(*list_of_lists))


def unique(list_: List) -> List:
    """Remove duplicate entries from list, keeping it in its original order

    >>> unique([1, 2, 2, 3, 4, 6, 2, 5])
    [1, 2, 3, 4, 6, 5]

    >>> unique(['bb', 'aa', 'aa', 'aa', 'aa', 'aa', 'bb'])
    ['bb', 'aa']
    """
    return list(collections.OrderedDict.fromkeys(list_))


def include_directives_from_kwargs(**kwargs) -> List[str]:
    """Turn "include_"-prefixed kwargs into list of strings for the request

    Arguments:
        All keyword arguments whose name consists of "include_*" and an
        entry of the INCLUDE enum are used to construct the output. All
        others are ignored.

    Known directives are included in the output if their value is truthy:

    >>> include_directives_from_kwargs(
    ...    include_datasheets=True, include_specs=True,
    ...    include_imagesets=False)
    ['datasheets', 'specs']

    Keyword args whose name starts with "include_" but don't match known
    directives trigger an exception:

    >>> include_directives_from_kwargs(include_abcdefg=True)
    Traceback (most recent call last):
        ...
    ValueError: abcdefg is not a known include directive

    However, keyword arguments not starting with "include_" are ignored
    silently:

    >>> include_directives_from_kwargs(abcdefg=True, include_specs=True)
    ['specs']
    """
    includes = []

    for kw_key, kw_val in kwargs.items():
        # filter for kwargs named include_* and value True
        if kw_key.startswith('include_') and kw_val:
            _, incl_key = kw_key.split('include_')
            # only accept documented values for the include directive
            if hasattr(IncludeDirectives, incl_key):
                includes.append(incl_key)
            else:
                raise ValueError(
                    f"{incl_key} is not a known include directive")

    return includes

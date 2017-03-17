"""
Top-level API, provides access to the Octopart API
without directly instantiating a client object.

Also wraps the response JSON in types that provide easier access
to various fields.
"""

import itertools
from concurrent.futures import ThreadPoolExecutor

from octopart import utils
from octopart.client import OctopartClient
from octopart.models import PartsMatchResult
from octopart.models import PartsSearchResult


MAX_REQUEST_THREADS = 10


def match(mpns,
          sellers=None,
          limit=None,
          specs=False,
          imagesets=False,
          descriptions=False,
          datasheets=False):
    """
    Match a list of MPNs against Octopart.

    Args:
        mpns (list): list of str MPNs

    Kwargs:
        sellers (list): list of str part sellers
        specs (bool): whether to include specs for parts
        imagesets (bool): whether to include imagesets for parts
        descriptions (bool): whether to include descriptions for parts

    Returns:
        list of `models.PartsMatchResult` objects.
    """
    client = OctopartClient()
    unique_mpns = utils.unique(mpns)
    query_types = ('q', 'mpn_or_sku')

    if sellers is None:
        queries = [
            {
                query_type: mpn,
                'limit': limit,
                'reference': mpn,
            }
            for (mpn, query_type) in itertools.product(
                unique_mpns, query_types)
        ]
    else:
        queries = [
            {
                query_type: mpn,
                'seller': seller,
                'limit': limit,
                'reference': mpn,
            }
            for (mpn, query_type, seller) in itertools.product(
                unique_mpns, query_types, sellers)
        ]

    def _request_chunk(chunk):
        return client.match(
            queries=chunk,
            specs=specs,
            imagesets=imagesets,
            descriptions=descriptions,
            datasheets=datasheets)

    # Execute API calls concurrently to significantly speed up
    # issuing multiple HTTP requests.
    with ThreadPoolExecutor(max_workers=MAX_REQUEST_THREADS) as pool:
        responses = pool.map(_request_chunk, utils.chunked(queries))

    return [
        PartsMatchResult(result)
        for response in responses
        for result in response['results']
    ]


def search(query,
           start=0,
           limit=10,
           sortby=(),
           filter_fields=None,
           filter_queries=None):
    """
    Search Octopart for a general keyword (and optional filters).

    Args:
        query (str): Free-form keyword query

    Kwargs:
        start (int): Ordinal position of first result
        limit (int): Maximum number of results to return
        sortby (list): [(fieldname, order)] list of tuples
        filter_fields (dict): {fieldname: value} dict
        filter_queries (dict): {fieldname: value} dict

    Returns:
        list of `models.PartsSearchResult` objects.
    """
    client = OctopartClient()
    response = client.search(
        query,
        start=start,
        limit=limit,
        sortby=sortby,
        filter_fields=filter_fields,
        filter_queries=filter_queries)
    return PartsSearchResult(response)

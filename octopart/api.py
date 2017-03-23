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


class MatchType(object):
    """
    Octopart 'match' query types. For more detail, see:
    https://octopart.com/api/docs/v3/rest-api#response-schemas-partsmatchquery
    """
    ALL = 'q'
    MPN = 'mpn'
    SKU = 'sku'
    MPN_OR_SKU = 'mpn_or_sku'


def match(mpns,
          match_type=MatchType.MPN_OR_SKU,
          partial_match=False,
          limit=3,
          sellers=(),
          specs=False,
          imagesets=False,
          descriptions=False,
          datasheets=False):
    """
    Match a list of MPNs against Octopart.

    Args:
        mpns (list): list of str MPNs

    Kwargs:
        partial_match (bool): whether to surround 'mpns' in wildcards
            to perform a partial part number match.
        limit (int): maximum number of results to return for each MPN
        sellers (list): list of str part sellers
        specs (bool): whether to include specs for parts
        imagesets (bool): whether to include imagesets for parts
        descriptions (bool): whether to include descriptions for parts

    Returns:
        list of `models.PartsMatchResult` objects.
    """
    client = OctopartClient()
    unique_mpns = utils.unique(mpns)
    if partial_match:
        # Append each MPN with a wildcard character so that Octopart performs
        # a partial match.
        unique_mpns = ['%s*' % mpn for mpn in unique_mpns]

    if not sellers:
        queries = [
            {
                match_type: mpn,
                'limit': limit,
                'reference': mpn,
            }
            for mpn in unique_mpns
        ]
    else:
        queries = [
            {
                match_type: mpn,
                'seller': seller,
                'limit': limit,
                'reference': mpn,
            }
            for (mpn, seller) in itertools.product(unique_mpns, sellers)
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

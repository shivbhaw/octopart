"""
Top-level API, provides access to the Octopart API
without directly instantiating a client object.

Also wraps the response JSON in types that provide easier access
to various fields.
"""

from concurrent.futures import ThreadPoolExecutor
import itertools
import typing as t

from octopart import models
from octopart import utils
from octopart.client import OctopartClient
from octopart.directives import include_directives_from_kwargs

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


def match(mpns: t.List[str],
          match_types: t.Optional[t.Tuple[str]] = None,
          partial_match: t.Optional[bool] = False,
          limit: t.Optional[int] = 3,
          sellers: t.Optional[t.Tuple[str]] = None,
          show: t.Optional[t.List[str]] = None,
          hide: t.Optional[t.List[str]] = None,
          **kwargs
          ) -> t.List[models.PartsMatchResult]:
    """
    Match a list of MPNs against Octopart.

    Args:
        mpns: list of str MPNs

    Kwargs:
        partial_match: whether to surround 'mpns' in wildcards to perform a
            partial part number match.
        limit: maximum number of results to return for each MPN
        sellers: list of str part sellers
        include_*, e.g. include_cad_models (bool): by setting to True, the
            corresponding field is set in the include directive of the
            Octopart API call, resulting in optional information being
            returned (see enum `IncludeDirectives` in directives.py for list of
            possible argument names)

    Returns:
        list of `models.PartsMatchResult` objects.
    """
    unique_mpns = utils.unique(mpns)
    match_types = match_types or (MatchType.MPN_OR_SKU,)
    sellers = sellers or ()

    if partial_match:
        # Append each MPN with a wildcard character so that Octopart performs
        # a partial match.
        unique_mpns = [f'{mpn}*' for mpn in unique_mpns]

    if not sellers:
        queries = [
            {
                match_type: mpn,
                'limit': limit,
                'reference': mpn,
            }
            for (match_type, mpn) in itertools.product(
                match_types, unique_mpns)
        ]
    else:
        queries = [
            {
                match_type: mpn,
                'seller': seller,
                'limit': limit,
                'reference': mpn,
            }
            for (match_type, mpn, seller) in itertools.product(
                match_types, unique_mpns, sellers)
        ]

    # assemble include[] directives as per
    # https://octopart.com/api/docs/v3/rest-api#include-directives
    includes = include_directives_from_kwargs(**kwargs)

    client = OctopartClient()

    def _request_chunk(chunk):
        return client.match(
            queries=chunk,
            includes=includes,
            show=show or [],
            hide=hide or [],
        )

    # Execute API calls concurrently to significantly speed up
    # issuing multiple HTTP requests.
    with ThreadPoolExecutor(max_workers=MAX_REQUEST_THREADS) as pool:
        responses = pool.map(_request_chunk, utils.chunk_queries(queries))

    return [
        models.PartsMatchResult(result)
        for response in responses
        for result in response['results']
    ]


def search(query: str,
           start: int=0,
           limit: int=10,
           sortby: t.List[t.Tuple[str, str]]=None,
           filter_fields: t.Dict[str, str]=None,
           filter_queries: t.Dict[str, str]=None,
           show: t.List[str]=None,
           hide: t.List[str]=None,
           **kwargs
           ) -> models.PartsSearchResult:
    """
    Search Octopart for a general keyword (and optional filters).

    Args:
        query (str): Free-form keyword query

    Kwargs:
        start: Ordinal position of first result
        limit: Maximum number of results to return
        sortby: [(fieldname, order)] list of tuples
        filter_fields: {fieldname: value} dict
        filter_queries: {fieldname: value} dict
        include_*, e.g. include_cad_models (bool): by setting to True, the
            corresponding field is set in the include directive of the
            Octopart API call, resulting in optional information being
            returned (see enum `INCLUDES` for list of possible argument
            names)

    Returns:
        list of `models.PartsSearchResult` objects.
    """
    # assemble include[] directives as per
    # https://octopart.com/api/docs/v3/rest-api#include-directives
    includes = include_directives_from_kwargs(**kwargs)

    client = OctopartClient()
    response = client.search(
        query,
        start=start,
        limit=limit,
        sortby=sortby,
        filter_fields=filter_fields,
        filter_queries=filter_queries,
        includes=includes,
        show=show,
        hide=hide,
    )
    return models.PartsSearchResult(response)


def get_brand(uid: str) -> models.Brand:
    client = OctopartClient()
    brand_dict = client.get_brand(uid)
    return models.Brand(brand_dict)


def search_brand(query: str,
                 start: t.Optional[int] = None,
                 limit: t.Optional[int] = None,
                 sortby: t.Optional[t.List[t.Tuple[str, str]]] = None,
                 ) -> t.List[models.Brand]:
    client = OctopartClient()
    res = client.search_brand(
        query=query, start=start, limit=limit, sortby=sortby)
    return [models.Brand(bd.get('item', {})) for bd in res.get('results', [])]


def get_category(uid: str) -> models.Category:
    client = OctopartClient()
    cat_dict = client.get_category(uid)
    return models.Category(cat_dict, strict=False)


def search_category(query: str,
                    start: t.Optional[int] = None,
                    limit: t.Optional[int] = None,
                    sortby: t.Optional[t.List[t.Tuple[str, str]]] = None,
                    ) -> t.List[models.Category]:
    client = OctopartClient()
    res = client.search_category(
        query=query, start=start, limit=limit, sortby=sortby)
    return [
        models.Category(bd.get('item', {}), strict=False)
        for bd in res.get('results', [])
    ]


def get_seller(uid: str) -> models.Seller:
    client = OctopartClient()
    slr_dict = client.get_seller(uid)
    return models.Seller(slr_dict, strict=False)


def search_seller(query: str,
                  start: t.Optional[int] = None,
                  limit: t.Optional[int] = None,
                  sortby: t.Optional[t.List[t.Tuple[str, str]]] = None,
                  ) -> t.List[models.Seller]:
    client = OctopartClient()
    res = client.search_seller(
        query=query, start=start, limit=limit, sortby=sortby)
    return [
        models.Seller(res.get('item', {}), strict=False)
        for res in res.get('results', [])
    ]

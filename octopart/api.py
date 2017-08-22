"""
Top-level API, provides access to the Octopart API
without directly instantiating a client object.

Also wraps the response JSON in types that provide easier access
to various fields.
"""

from concurrent.futures import ThreadPoolExecutor
import itertools
from typing import Dict, List, Tuple
import warnings

from . import models
from . import utils
from .client import OctopartClient
from .directives import include_directives_from_kwargs

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


def match(
        mpns: List[str],
        match_types: Tuple[str]=None,
        partial_match: bool=False,
        limit: int=3,
        sellers: Tuple[str]=None,
        specs: bool=False,  # deprecated, use include_imagesets
        imagesets: bool=False,  # deprecated, use include_imagesets
        descriptions: bool=False,  # deprecated, use include_imagesets
        datasheets: bool=False,  # deprecated, use include_imagesets
        show: List[str]=None,
        hide: List[str]=None,
        **kwargs) -> List[models.PartsMatchResult]:
    """
    Match a list of MPNs against Octopart.

    Args:
        mpns: list of str MPNs

    Kwargs:
        partial_match: whether to surround 'mpns' in wildcards to perform a
            partial part number match.
        limit: maximum number of results to return for each MPN
        sellers: list of str part sellers
        specs: whether to include specs for each part, obsolete and superseded
            by include_specs
        imagesets: whether to include imagesets for each part, obsolete and
            superseded by include_imagesets
        descriptions: whether to include descriptions for each part, obsolete
            and superseded by include_descriptions
        datasheets: whether to include datasheet links for each part, obsolete
            and superseded by include_datasheets
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

    # backward compatibility for other methods of specifying include directives
    if specs:
        includes.append('specs')
        warnings.warn(
            "The specs argument is deprecated, use include_specs argument "
            "instead.", DeprecationWarning)
    if imagesets:
        includes.append('imagesets')
        warnings.warn(
            "The imagesets argument is deprecated, use include_imagesets "
            "argument instead.", DeprecationWarning)
    if descriptions:
        includes.append('descriptions')
        warnings.warn(
            "The descriptions argument is deprecated, use "
            "include_descriptions argument instead.", DeprecationWarning)
    if datasheets:
        includes.append('datasheets')
        warnings.warn(
            "The datasheets argument is deprecated, use "
            "include_datasheets argument instead.", DeprecationWarning)

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


def search(
        query: str,
        start: int=0,
        limit: int=10,
        sortby: List[Tuple[str, str]]=None,
        filter_fields: Dict[str, str]=None,
        filter_queries: Dict[str, str]=None,
        show: List[str]=None,
        hide: List[str]=None,
        **kwargs) -> models.PartsSearchResult:
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


def search_brand(
        query: str,
        start: int=None,
        limit: int=None,
        sortby: str=None,
        ) -> List[models.Brand]:
    client = OctopartClient()
    res = client.search_brand(
        query=query, start=start, limit=limit, sortby=sortby)
    return [models.Brand(bd.get('item', {})) for bd in res.get('results', [])]

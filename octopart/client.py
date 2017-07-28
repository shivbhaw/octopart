import copy
import enum
import json
import logging
import os
from typing import Any, Collection, Dict, List
import warnings

import requests

from octopart import models
from octopart.exceptions import OctopartError
from octopart.decorators import retry

logger = logging.getLogger(__name__)


class INCLUDE(str, enum.Enum):
    """Categories of information that can optionally be requested

    These categories may be included in the include[] request parameter to
    request additional information in the response content.

    API docs: https://octopart.com/api/docs/v3/rest-api#include-directives
    """
    short_description = 'short_description'
    datasheets = 'datasheets'
    compliance_documents = 'compliance_documents'
    descriptions = 'descriptions'
    imagesets = 'imagesets'
    specs = 'specs'
    category_uids = 'category_uids'
    external_links = 'external_links'
    reference_designs = 'reference_designs'
    cad_models = 'cad_models'


DEFAULT_BASE_URL = 'https://octopart.com/api/v3'


class OctopartClient(object):
    """Client object for Octopart API v3

    Visit https://octopart.com/api/register to get an API key, then set it as
    an environment variable named 'OCTOPART_API_KEY', or pass the key directly
    to this constructor.
    """

    def __init__(
            self, api_key: str=None, base_url: str=DEFAULT_BASE_URL) -> None:
        """
        Kwargs:
            api_key (str): Octopart API key
        """
        api_key = api_key or os.getenv('OCTOPART_API_KEY')
        if not api_key:
            raise ValueError(
                "API key must be set. "
                "Set 'OCTOPART_API_KEY' as an environment variable, "
                "or pass your key directly to the client."
            )
        self.api_key = api_key
        self.base_url = base_url

    @property
    def api_key_param(self) -> Dict[str, str]:
        return {'apikey': self.api_key}

    @retry
    def _request(
            self,
            path: str,
            params: Dict[str, Any]=None
            ) -> Any:
        params = copy.copy(params or {})
        params.update(self.api_key_param)

        response = requests.get('%s%s' % (self.base_url, path), params=params)
        logger.debug('requested Octopart URI: %s', response.url)

        response.raise_for_status()
        return response.json()

    def match(
            self,
            queries: Collection[models.PartsMatchQuery]=(),
            specs: bool=False,  # deprecated, use include_specs
            imagesets: bool=False,  # deprecated, use include_imagesets
            descriptions: bool=False,  # deprecated, use include_descriptions
            datasheets: bool=False,  # deprecated, use include_datasheets
            exact_only: bool=False,
            **kwargs) -> Dict[str, Any]:
        """
        Search for parts by MPN, brand, SKU, or other fields.
        See `models.PartsMatchQuery` for the full field list.

        NOTE: Octopart allows up to 20 queries to be batched together
        in a single request to this endpoint.

        Args:
            queries (list): list of part queries. See `models.PartsMatchQuery`
                for required fields in each query.
            specs (bool): whether to include specs for each part, obsolete and
                superseded by include_specs
            imagesets (bool): whether to include imagesets for each part,
                obsolete and superseded by include_imagesets
            descriptions (bool): whether to include descriptions for each part,
                obsolete and superseded by include_descriptions
            datasheets (bool): whether to include datasheet links for each
                part, obsolete and superseded by include_datasheets
            exact_only (bool): whether to match non-alphanumeric characters in
                MPNs and SKUs
            include_*, e.g. include_cad_models (bool): by setting to True, the
                corresponding field is set in the include directive of the
                Octopart API call, resulting in optional information being
                returned (see enum `INCLUDES` for list of possible argument
                names)

        Returns:
            dict. See `models.PartsMatchResponse` for exact fields.
        """
        if len(queries) > 20:
            raise ValueError(
                'Expected `queries` to be < 20 elements. Saw: %s' % queries)

        # Validate `queries` format.
        if not models.PartsMatchQuery.is_valid_list(queries):
            errors = models.PartsMatchQuery.errors_list(queries)
            raise OctopartError('Queries are malformed: %s' % errors)

        # endpoint specific parameters as per
        # https://octopart.com/api/docs/v3/rest-api#endpoints-parts-match
        params: Dict[str, Any] = {'queries': json.dumps(queries)}

        # since there is a maximum URL length, only set exact_only parameter in
        # the URL when using the non-default value
        if exact_only:
            params['exact_only'] = 'true'

        # assemble include[] directives as per
        # https://octopart.com/api/docs/v3/rest-api#include-directives
        includes = self._include_directives(
            **{k: v for k, v in kwargs.items() if k.startswith('include_')})

        # backward compatibility for other methods of specifying include
        # directives
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

        params['include[]'] = includes

        return self._request('/parts/match', params=params)

    def search(
            self,
            query: str,
            start: int=0,
            limit: int=10,
            sortby: Collection=(),
            filter_fields: dict=None,
            filter_queries: dict=None,
            **kwargs) -> dict:
        """
        Search for parts, using more fields and filter options than 'match'.

        Args:
            query (str): free-form keyword query

        Kwargs:
            start (int): ordinal position of first result
            limit (int): maximum number of results to return
            sortby (list): [(fieldname, order)] list of tuples
            filter_fields (dict): {fieldname: value} dict,
                values are filtered exactly
            filter_queries (dict): {fieldname: value} dict,
                values can be more complex. See for details:
                https://octopart.com/api/docs/v3/search-tutorial#filter-queries

        Returns:
            dict. See `models.PartsSearchResponse` for exact fields.
        """
        filter_fields = filter_fields or {}
        filter_queries = filter_queries or {}

        sortby_param = ', '.join([
            '%s %s' % (sort_value, sort_order)
            for sort_value, sort_order in sortby
        ])

        filter_fields_param = {
            'filter[fields][%s][]' % field: value
            for field, value in filter_fields.items()
        }

        filter_queries_param = {
            'filter[queries][]': '%s:%s' % (field, value)
            for field, value in filter_queries.items()
        }

        data = {
            'q': query,
            'start': start,
            'limit': limit,
            'sortby': sortby_param,
            'filter_fields': filter_fields_param,
            'filter_queries': filter_queries_param
        }

        if not models.PartsSearchQuery.is_valid(data):
            errors = models.PartsSearchQuery.errors(data)
            raise OctopartError('Query is malformed: %s' % errors)

        # Convert `query` to format that Octopart accepts.
        params = models.PartsSearchQuery(data).to_primitive()
        params.update(params.pop('filter_fields'))
        params.update(params.pop('filter_queries'))

        # assemble include[] directives as per
        # https://octopart.com/api/docs/v3/rest-api#include-directives
        includes = self._include_directives(
            **{k: v for k, v in kwargs.items() if k.startswith('include_')})
        params.update({'include[]': includes})

        return self._request('/parts/search', params=params)

    @staticmethod
    def _include_directives(**kwargs) -> List[str]:
        """Turn "include_"-prefixed kwargs into list of strings for the request

        Arguments:
            All keyword arguments whose name consists of "include_*" and an
            entry of the INCLUDE enum are used to construct the output. All
            others are ignored.

        >>> OctopartClient._include_directives(
        ...    include_datasheets=True, include_specs=True,
        ...    include_imagesets=False)
        ['datasheets', 'specs']

        >>> OctopartClient._include_directives(
        ...    include_abcdefg=True, abcdefg_specs=True)
        []
        """
        includes = []

        for kw_key, kw_val in kwargs.items():
            # filter for kwargs named include_* and value True
            if kw_key.startswith('include_') and kw_val:
                _, incl_key = kw_key.split('include_')
                # only accept documented values for the include directive
                if hasattr(INCLUDE, incl_key):
                    includes.append(incl_key)

        return includes

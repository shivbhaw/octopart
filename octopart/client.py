import copy
import json
import logging
import os
from typing import Any, Collection, Dict, List

import requests

from octopart import models
from octopart.exceptions import OctopartError
from octopart.decorators import retry

logger = logging.getLogger(__name__)


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
            queries: Collection[models.PartsMatchQuery],
            exact_only: bool=False,
            includes: List[str]=None,
            ) -> Dict[str, Any]:
        """
        Search for parts by MPN, brand, SKU, or other fields, sending up to 20
        queries at the same time. See `models.PartsMatchQuery` for the full
        field list that may be used in each query.

        This calls the /parts/match endpoint of the Octopart API:
        https://octopart.com/api/docs/v3/rest-api#endpoints-parts-match

        Args:
            queries: list of part queries. See `models.PartsMatchQuery` for
                required fields in each query.
            exact_only: whether to match non-alphanumeric characters in MPNs
                and SKUs
            includes: List of strings to be sent as "include directives" of the
                Octopart API call, resulting in optional information being
                returned (see enum `IncludeDirectives` in directives.py for
                list of possible argument names)

        Returns:
            dict. See `models.PartsMatchResponse` for exact fields.
        """
        if len(queries) > 20:
            raise ValueError(
                'Expected `queries` to be < 20 elements. Saw: %s' % queries)

        # validate `queries` format
        if not models.PartsMatchQuery.is_valid_list(queries):
            errors = models.PartsMatchQuery.errors_list(queries)
            raise OctopartError('Queries are malformed: %s' % errors)

        # required params for /part/match API call, as per
        # https://octopart.com/api/docs/v3/rest-api#endpoints-parts-match
        params: Dict[str, Any] = {'queries': json.dumps(queries)}

        # since there is a maximum URL length, only set options parameters in
        # the URL when using the non-default value
        if exact_only:
            params['exact_only'] = 'true'
        if includes:
            params['include[]'] = includes

        return self._request('/parts/match', params=params)

    def search(
            self,
            query: str,  # maps to "q" parameter in Octopart API
            start: int=0,
            limit: int=10,
            sortby: list=None,
            filter_fields: dict=None,
            filter_queries: dict=None,
            includes: List[str]=None,
            ) -> dict:
        """
        Search for parts, using more fields and filter options than 'match'.

        This calls the /parts/search endpoint of the Octopart API:
        https://octopart.com/api/docs/v3/rest-api#endpoints-parts-search

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
        sortby = sortby or []

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

        # since there is a maximum URL length, only set options parameters in
        # the URL when using the non-default value
        if includes:
            params['include[]'] = includes

        return self._request('/parts/search', params=params)

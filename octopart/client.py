import copy
import json
import logging
import os
import typing as t

import requests

from octopart import models
from octopart.exceptions import OctopartError
from octopart.decorators import retry
from octopart.utils import sortby_param_str_from_list

logger = logging.getLogger(__name__)


DEFAULT_BASE_URL = 'https://octopart.com/api/v3'


class OctopartClient(object):
    """Client object for Octopart API v3

    Visit https://octopart.com/api/register to get an API key, then set it as
    an environment variable named 'OCTOPART_API_KEY', or pass the key directly
    to this constructor.
    """

    def __init__(self,
                 api_key: t.Optional[str] = None,
                 base_url: t.Optional[str] = DEFAULT_BASE_URL
                 ) -> None:
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
    def api_key_param(self) -> t.Dict[str, str]:
        return {'apikey': self.api_key}

    @retry
    def _request(self,
                 path: str,
                 params: t.Dict[str, t.Any]=None
                 ) -> t.Any:
        params = copy.copy(params or {})
        params.update(self.api_key_param)

        response = requests.get('%s%s' % (self.base_url, path), params=params)
        logger.debug('Requested Octopart URI: %s', response.url)

        response.raise_for_status()
        return response.json()

    def match(self,
              queries: t.Collection[models.PartsMatchQuery],
              exact_only: t.Optional[bool] = False,
              includes: t.Optional[t.List[str]] = None,
              hide: t.Optional[t.List[str]] = None,
              show: t.Optional[t.List[str]] = None,
              ) -> t.Dict[str, t.Any]:
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
            hide: List of strings to be sent as "hide directives" of the
                Octopart API call, resulting in certain fields being excluded
                from the response. See note below.
            show: Inverse of `hide`. See note below.

        Refer to https://octopart.com/api/docs/v3/rest-api#show-hide-directives
        for usage information of the `hide` and `show` directives.

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
        params: t.Dict[str, t.Any] = {'queries': json.dumps(queries)}

        # since there is a maximum URL length, only set options parameters in
        # the URL when using the non-default value
        if exact_only:
            params['exact_only'] = 'true'
        if includes:
            params['include[]'] = includes
        if show:
            params['show[]'] = show
        if hide:
            params['hide[]'] = hide

        return self._request('/parts/match', params=params)

    def search(self,
               query: str,  # maps to "q" parameter in Octopart API
               start: int=0,
               limit: int=10,
               sortby: t.Optional[t.List[t.Tuple[str, str]]] = None,
               filter_fields: t.Optional[dict] = None,
               filter_queries: t.Optional[dict] = None,
               includes: t.Optional[t.List[str]] = None,
               hide: t.Optional[t.List[str]] = None,
               show: t.Optional[t.List[str]] = None,
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
            includes, hide, show: Same as `match()`.

        Returns:
            dict. See `models.PartsSearchResponse` for exact fields.
        """
        filter_fields = filter_fields or {}
        filter_queries = filter_queries or {}

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
            'sortby': sortby_param_str_from_list(sortby) or None,
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
        if show:
            params['show[]'] = show
        if hide:
            params['hide[]'] = hide

        return self._request('/parts/search', params=params)

    def get_brand(self, uid: str) -> dict:
        """Retrieve brand data by UID

        This calls the /brands/ endpoint of the Octopart API:
        https://octopart.com/api/docs/v3/rest-api#endpoints-brands-get

        Args:
            uid (str): An Octopart brand UID

        Returns:
            dict. See `models.Brand` for exact fields.
        """
        return self._request(f'/brands/{uid}')

    def search_brand(self,
                     query: str,
                     start: t.Optional[int] = None,
                     limit: t.Optional[int] = None,
                     sortby: t.Optional[t.List[t.Tuple[str, str]]] = None,
                     ) -> dict:
        """Search for manufacturer names by keyword.

        From the API docs: "This is the ideal method to use to go from a brand
        alias or keyword to a Octopart brand instance"

        This calls the /brands/searc endpoint of the Octopart API:
        https://octopart.com/api/docs/v3/rest-api#endpoints-brands-search

        "brand" vs "manufacturer": For a given part, the Octopart API returns
        brand and manufacturer information. The schemas for Brand and
        Manufacturer are identical and include a uid, name, and homepage_url.
        Even though different uids are returned for the brand and manufacturer
        of a part, the content (name and homepage_url) of the two objects will
        always be identical (source: conversation in Octopart's support Slack
        channel).
        """
        params = {
            'q': query,
            'start': start,
            'limit': limit,
            'sortby': sortby_param_str_from_list(sortby),
        }

        # drop None-valued parameters
        params = {k: v for k, v in params.items() if v is not None}

        return self._request('/brands/search', params=params)

    def get_category(self, uid: str) -> dict:
        """Retrieve category information by UID

        This calls the /categories/ endpoint of the Octopart API:
        https://octopart.com/api/docs/v3/rest-api#endpoints-categories-get

        Args:
            uid (str): An Octopart category UID
        """
        return self._request(f'/categories/{uid}')

    def search_category(self,
                        query: str,
                        start: t.Optional[int] = None,
                        limit: t.Optional[int] = None,
                        sortby: t.Optional[t.List[t.Tuple[str, str]]] = None,
                        include_imagesets: t.Optional[bool] = None,
                        ) -> dict:
        """Search for Octopart categories by keyword.

        This calls the /categories/search endpoint of the Octopart API:
        https://octopart.com/api/docs/v3/rest-api#endpoints-categories-search
        """
        params = {
            'q': query,
            'start': start,
            'limit': limit,
            'sortby': sortby_param_str_from_list(sortby) or None,
            'include[]': ['imagesets'] if include_imagesets else None,
        }

        # drop None-valued parameters
        params = {k: v for k, v in params.items() if v is not None}

        return self._request('/categories/search', params=params)

    def get_seller(self, uid: str) -> dict:
        """Retrieve category information by UID

        This calls the /sellers/ endpoint of the Octopart API:
        https://octopart.com/api/docs/v3/rest-api#endpoints-sellers-get

        Args:
            uid (str): An Octopart seller UID
        """
        return self._request(f'/sellers/{uid}')

    def search_seller(self,
                      query: str,
                      start: t.Optional[int] = None,
                      limit: t.Optional[int] = None,
                      sortby: t.Optional[t.List[t.Tuple[str, str]]] = None,
                      ) -> dict:
        """Search for Octopart sellers by keyword.

        This calls the /sellers/search endpoint of the Octopart API:
        https://octopart.com/api/docs/v3/rest-api#endpoints-sellers-search
        """
        params = {
            'q': query,
            'start': start,
            'limit': limit,
            'sortby': sortby_param_str_from_list(sortby) or None,
        }

        # drop None-valued parameters
        params = {k: v for k, v in params.items() if v is not None}

        return self._request('/sellers/search', params=params)

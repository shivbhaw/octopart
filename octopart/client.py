import json
import logging
import os

import requests
from requests.exceptions import HTTPError

from octopart import models
from octopart.exceptions import OctopartError

logger = logging.getLogger(__name__)


class OctopartClient(object):
    """
    Client object for Octopart API v3.

    Visit https://octopart.com/api/register to get an API key, then set it as
    an environment variable named 'OCTOPART_API_KEY', or pass the key directly
    to this constructor.
    """
    BASE_URI = 'https://octopart.com/api/v3'

    def __init__(self, api_key=None):
        """
        Kwargs:
            api_key (str): Octopart API key
        """
        api_key = os.getenv('OCTOPART_API_KEY') or api_key
        if not api_key:
            raise ValueError(
                "API key must be set. "
                "Set 'OCTOPART_API_KEY' as an environment variable, "
                "or pass your key directly to the client."
            )
        self.api_key = api_key

    @property
    def api_key_param(self):
        return {'apikey': self.api_key}

    def _request(self, path, params=None):
        params = params or {}
        # `requests` allows query params to be a dict, or a list of 2-tuples.
        # The latter is nice because Octopart requires identical keys for
        # certain resources, like specs and imagesets.
        if isinstance(params, dict):
            params.update(self.api_key_param)
        else:
            params.extend(self.api_key_param.items())

        response = requests.get('%s%s' % (self.BASE_URI, path), params=params)
        logger.debug('requested Octopart URI: %s', response.url)

        try:
            response.raise_for_status()
        except HTTPError as err:
            raise OctopartError('HTTP error: %s' % err.message)
        return response.json()

    def match(self,
              queries=(),
              specs=False,
              imagesets=False,
              descriptions=False,
              exact_match=False):
        """
        Search for parts by MPN, brand, SKU, or other fields.
        See `models.PartsMatchQuery` for the full field list.

        NOTE: Octopart allows up to 20 queries to be batched together
        in a single request to this endpoint.

        Args:
            queries (list): list of part queries. See `models.PartsMatchQuery`
                for required fields in each query.
            specs (bool): whether to include specs for each part
            imagesets (bool): whether to include imagesets for each part
            descriptions (bool): whether to include descriptions for each part
            exact_match (bool): match non-alphanumeric chars in MPNs and SKUs.

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

        params = [('queries', json.dumps(queries))]
        if specs:
            params.append(('include[]', 'specs'))
        if imagesets:
            params.append(('include[]', 'imagesets'))
        if descriptions:
            params.append(('include[]', 'descriptions'))

        return self._request('/parts/match', params=params)

    def search(self,
               query,
               start=0,
               limit=10,
               sortby=(),
               filter_fields=None,
               filter_queries=None):
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
            for field, value in filter_fields.iteritems()
        }

        filter_queries_param = {
            'filter[queries][]': '%s:%s' % (field, value)
            for field, value in filter_queries.iteritems()
        }

        query = models.PartsSearchQuery({
            'q': query,
            'start': start,
            'limit': limit,
            'sortby': sortby_param,
            'filter_fields': filter_fields_param,
            'filter_queries': filter_queries_param
        })

        if query.errors:
            raise OctopartError('Query is malformed: %s' % query.errors)

        params = query.to_primitive()
        params.update(params.pop('filter_fields'))
        params.update(params.pop('filter_queries'))

        return self._request('/parts/search', params=params)

from contextlib import contextmanager
from unittest import TestCase
from unittest.mock import patch
import re

import responses

from octopart.client import OctopartClient
from octopart.exceptions import OctopartError


@contextmanager
def octopart_mock_response():
    """Boilerplate for mocking all Octopart API URLs with an empty response"""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            re.compile(r'https://octopart\.com/api/v3/.*'),
            body='{}',
            status=200,
            content_type='application/json'
        )

        yield rsps


def request_url_from_request_mock(reqmock):
    """Given responses.RequestsMock, get URL of first recorded request

    Utility method for asserting that the correct URL was generated. Fails
    if more than one request was made against the RequestMock.
    """
    assert len(reqmock.calls) == 1
    request, _ = reqmock.calls[0]
    return request.url


class ClientTests(TestCase):
    """Tests for client initialization and configuration"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    def test_missing_api_token(self):
        with self.assertRaises(ValueError):
            OctopartClient()

    def test_malformed_search_query(self):
        client = OctopartClient(api_key='TEST_TOKEN')
        with self.assertRaises(OctopartError):
            client.search(["query1", "query2"])

    def test_bad_api_token(self):
        client = OctopartClient(api_key='BAD_TOKEN')
        with self.assertRaises(OctopartError):
            client.match([{'q': 'RUM001L02T2CL'}])
            assert 'include%5B%5D=imagesets' in called_url  # %5B%5D is []

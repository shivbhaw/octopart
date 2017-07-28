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


class PartMatchTests(TestCase):
    """Tests for the client's match() method"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    @patch('requests.get')
    def test_too_many_match_queries(self, mock_get):
        queries = [{'q': 'fake-mpn'}] * 21
        with self.assertRaises(ValueError):
            self.client.match(queries)
        # the exception should prevent any queries from being made
        assert not mock_get.called

    @patch('requests.get')
    def test_malformed_match_query(self, mock_get):
        with self.assertRaises(OctopartError):
            self.client.match([{'q': ["not", "a", "string"]}])
        # the exception should prevent any queries from being made
        assert not mock_get.called

    def test_exact_match_true(self):
        with octopart_mock_response() as rsps:
            self.client.match([{'q': 'FAKE_MPN'}], exact_only=True)
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/match' in called_url
            assert 'exact_only=true' in request_url_from_request_mock(rsps)

    def test_exact_match_false(self):
        with octopart_mock_response() as rsps:
            self.client.match([{'q': 'FAKE_MPN'}])
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/match' in called_url
            assert 'exact_only=' not in called_url

    def test_deprecated_arguments(self):
        with octopart_mock_response() as rsps:
            with self.assertWarns(DeprecationWarning):
                self.client.match([{'q': 'FAKE_MPN'}], datasheets=True)
            called_url = request_url_from_request_mock(rsps)
            assert 'include%5B%5D=datasheets' in called_url  # %5B%5D is []

    def test_complete_example(self):
        with octopart_mock_response() as rsps:
            self.client.match([
                {'mpn': 'MPN1', 'brand': 'Brand 1'},
                {'mpn_or_sku': 'MPN-or#SKU2'},
            ], exact_only=True, include_imagesets=True)
            called_url = request_url_from_request_mock(rsps)

            # %22brand%22%3A+%22Brand+1%22 is "brand": "Brand 1"
            assert '%22brand%22%3A+%22Brand+1%22' in called_url
            # %22mpn%22%3A+%22MPN1%22 is "mpn": "MPN1"
            assert '%22mpn%22%3A+%22MPN1%22' in called_url
            # %22mpn_or_sku%22%3A+%22MPN-or%23SKU2%22%7D%5D is
            # "22mpn_or_sku": "MPN-or#SKU2"
            assert '%22mpn_or_sku%22%3A+%22MPN-or%23SKU2%22%' in called_url
            assert 'exact_only=true' in called_url
            assert 'include%5B%5D=imagesets' in called_url  # %5B%5D is []

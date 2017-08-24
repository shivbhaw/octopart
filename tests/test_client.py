import os
from unittest import TestCase
from unittest.mock import patch

from octopart.client import OctopartClient
from octopart.exceptions import OctopartError

from .utils import octopart_mock_response
from .utils import request_url_from_request_mock


class ClientTests(TestCase):
    """Tests for client initialization and configuration"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    def test_missing_api_token(self):
        # having the OCTOPART_API_KEY env var set could jinx this test, remove
        # it temporarily
        cached_env_var = os.environ.pop('OCTOPART_API_KEY', None)
        with self.assertRaises(ValueError):
            OctopartClient()
        # if env var was set before, resurrect it
        if cached_env_var:
            os.environ['OCTOPART_API_KEY'] = cached_env_var

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

    def test_hide_directive(self):
        with octopart_mock_response() as rsps:
            self.client.match([{'q': 'FAKE_MPN'}], hide=['offers'])
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/match' in called_url
            assert 'hide%5B%5D=offers' in called_url

    def test_show_directive(self):
        with octopart_mock_response() as rsps:
            self.client.match([{'q': 'FAKE_MPN'}], show=['offers', 'unicorns'])
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/match' in called_url
            assert 'show%5B%5D=offers' in called_url
            assert 'show%5B%5D=unicorns' in called_url

    def test_include_directive(self):
        with octopart_mock_response() as rsps:
            self.client.match([{'q': 'FAKE_MPN'}], includes=['cad_models'])
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/match' in called_url
            assert 'include%5B%5D=cad_models' in called_url

    def test_no_directives(self):
        with octopart_mock_response() as rsps:
            self.client.match([{'q': 'FAKE_MPN'}])
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/match' in called_url
            assert 'hide%5B%5D=' not in called_url
            assert 'show%5B%5D=' not in called_url
            assert 'include%5B%5D=' not in called_url
            assert 'exact_only=' not in called_url

    def test_complete_example(self):
        with octopart_mock_response() as rsps:
            self.client.match([
                {'mpn': 'MPN1', 'brand': 'Brand 1'},
                {'mpn_or_sku': 'MPN-or#SKU2'},
            ], exact_only=True, show=['brand.name'], includes=['imagesets'])
            called_url = request_url_from_request_mock(rsps)

            # %22brand%22%3A+%22Brand+1%22 is "brand": "Brand 1"
            assert '%22brand%22%3A+%22Brand+1%22' in called_url
            # %22mpn%22%3A+%22MPN1%22 is "mpn": "MPN1"
            assert '%22mpn%22%3A+%22MPN1%22' in called_url
            # %22mpn_or_sku%22%3A+%22MPN-or%23SKU2%22%7D%5D is
            # "22mpn_or_sku": "MPN-or#SKU2"
            assert '%22mpn_or_sku%22%3A+%22MPN-or%23SKU2%22%' in called_url
            assert 'exact_only=true' in called_url
            assert 'show%5B%5D=brand.name' in called_url
            assert 'include%5B%5D=imagesets' in called_url  # %5B%5D is []


class PartSearchTests(TestCase):
    """Tests for the client's search() method"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    @patch('requests.get')
    def test_malformed_match_query(self, mock_get):
        with self.assertRaises(OctopartError):
            self.client.search([{'query': ["not", "a", "string"]}])
        # the exception should prevent any queries from being made
        assert not mock_get.called

    def test_hide_directive(self):
        with octopart_mock_response() as rsps:
            self.client.search(query='resistor 10kohm 10%', hide=['offers'])
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/search' in called_url
            assert 'hide%5B%5D=offers' in called_url

    def test_show_directive(self):
        with octopart_mock_response() as rsps:
            self.client.search(
                query='resistor 10kohm 10%', show=['offers', 'unicorns'])
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/search' in called_url
            assert 'show%5B%5D=offers' in called_url
            assert 'show%5B%5D=unicorns' in called_url

    def test_include_directive(self):
        with octopart_mock_response() as rsps:
            self.client.search(
                query='resistor 10kohm 10%', includes=['cad_models'])
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/search' in called_url
            assert 'include%5B%5D=cad_models' in called_url

    def test_no_directives(self):
        with octopart_mock_response() as rsps:
            self.client.search(query='resistor 10kohm 10%')
            called_url = request_url_from_request_mock(rsps)
            assert '/parts/search' in called_url
            assert 'hide%5B%5D=' not in called_url
            assert 'show%5B%5D=' not in called_url
            assert 'include%5B%5D=' not in called_url

    def test_complete_example(self):
        with octopart_mock_response() as rsps:
            self.client.search(
                query='resistor 10kohm 10%',
                show=['brand.name'],
                includes=['imagesets'],
                start=50,
                limit=50,
                sortby=[('score', 'desc')],
            )
            called_url = request_url_from_request_mock(rsps)
            assert 'q=resistor+10kohm+10%25' in called_url
            assert 'sortby=score+desc' in called_url
            assert 'start=50' in called_url
            assert 'limit=50' in called_url
            assert 'show%5B%5D=brand.name' in called_url  # %5B%5D is []
            assert 'include%5B%5D=imagesets' in called_url


class BrandSearchTests(TestCase):
    """Tests for the client's search_brand() and get_brand() methods"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    def test_get_brand(self):
        with octopart_mock_response() as rsps:
            self.client.get_brand('brand_uuid')
            called_url = request_url_from_request_mock(rsps)
            assert '/brands/brand_uuid' in called_url

    def test_search_brand(self):
        with octopart_mock_response() as rsps:
            self.client.search_brand('MyBrandName')
            called_url = request_url_from_request_mock(rsps)
            assert '/brands/search' in called_url
            assert 'q=MyBrandName' in called_url


class CategorySearchTests(TestCase):
    """Tests for the client's search_category() and get_category() methods"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    def test_get_category(self):
        with octopart_mock_response() as rsps:
            self.client.get_category('cat_uuid')
            called_url = request_url_from_request_mock(rsps)
            assert '/categories/cat_uuid' in called_url

    def test_search_category(self):
        with octopart_mock_response() as rsps:
            self.client.search_category('Fluxistors')
            called_url = request_url_from_request_mock(rsps)
            assert '/categories/search' in called_url
            assert 'q=Fluxistors' in called_url


class SellerSearchTests(TestCase):
    """Tests for the client's search_seller() and get_seller() methods"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    def test_get_category(self):
        with octopart_mock_response() as rsps:
            self.client.get_seller('seller_uuid')
            called_url = request_url_from_request_mock(rsps)
            assert '/sellers/seller_uuid' in called_url

    def test_search_category(self):
        with octopart_mock_response() as rsps:
            self.client.search_seller('Mouser-Key')
            called_url = request_url_from_request_mock(rsps)
            assert '/sellers/search' in called_url
            assert 'q=Mouser-Key' in called_url

    def test_search_category_with_sortby(self):
        with octopart_mock_response() as rsps:
            self.client.search_seller('Mouser-Key', sortby=[('name', 'asc')])
            called_url = request_url_from_request_mock(rsps)
            assert '/sellers/search' in called_url
            assert 'q=Mouser-Key' in called_url
            assert 'sortby=name+asc' in called_url

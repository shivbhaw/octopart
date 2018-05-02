import os
from unittest import TestCase
from unittest.mock import patch

import pytest

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
        with pytest.raises(ValueError):
            OctopartClient()
        # if env var was set before, resurrect it
        if cached_env_var:
            os.environ['OCTOPART_API_KEY'] = cached_env_var

    def test_malformed_search_query(self):
        client = OctopartClient(api_key='TEST_TOKEN')
        with pytest.raises(OctopartError):
            client.search(["query1", "query2"])

    def test_bad_api_token(self):
        client = OctopartClient(api_key='BAD_TOKEN')
        with pytest.raises(OctopartError):
            client.match([{'q': 'RUM001L02T2CL'}])


class PartMatchTests(TestCase):
    """Tests for the client's match() method"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    @patch('requests.get')
    def test_too_many_match_queries(self, mock_get):
        queries = [{'q': 'fake-mpn'}] * 21
        with pytest.raises(ValueError):
            self.client.match(queries)
        # the exception should prevent any queries from being made
        assert not mock_get.called

    @patch('requests.get')
    def test_malformed_match_query(self, mock_get):
        with pytest.raises(OctopartError):
            self.client.match([{'q': ["not", "a", "string"]}])
        # the exception should prevent any queries from being made
        assert not mock_get.called

    def test_exact_match_true(self):
        response_body = {
            "__class__": "PartsMatchResponse",
            "results": [
                {
                    "__class__": "PartsMatchResult",
                    "items": []
                }
            ]
        }

        with octopart_mock_response(response_body) as response:
            dict_ = self.client.match(
                [{'q': 'ATTINY2313-20SU-zZz'}], exact_only=True)
            [result] = dict_['results']
            assert len(result['items']) == 0
            called_url = request_url_from_request_mock(response)
            assert '/parts/match' in called_url
            assert 'exact_only=true' in request_url_from_request_mock(response)

    def test_hide_directive(self):
        response_body = {
            "results": [
                {
                    "__class__": "PartsMatchResult",
                    "items": [
                        {
                            "__class__": "Part",
                            "brand": {
                                "__class__": "Brand",
                                "homepage_url": "http://www.microchip.com",
                                "name": "Microchip",
                                "uid": "ddaa1ca0f0300a6d"
                            },
                            "manufacturer": {
                                "__class__": "Manufacturer",
                                "homepage_url": "http://www.microchip.com",
                                "name": "Microchip",
                                "uid": "d78f1285fe150448"
                            },
                            "mpn": "ATTINY2313-20SU",
                            "octopart_url": "https://octopart.com/attiny2313-20su-microchip-77762028",  # noqa
                            "offers": [
                                {
                                    "__class__": "PartOffer",
                                    "eligible_region": "",
                                    "factory_lead_days": 94,
                                    "factory_order_multiple": None,
                                    "in_stock_quantity": 14517,
                                    "is_authorized": True,
                                    "is_realtime": False,
                                    "last_updated": "2018-04-30T12:26:55Z",
                                    "moq": 1,
                                    "multipack_quantity": None,
                                    "octopart_rfq_url": None,
                                    "on_order_eta": None,
                                    "on_order_quantity": None,
                                    "order_multiple": None,
                                    "packaging": "Tube",
                                    "prices": {
                                        "USD": [
                                            [1, "1.79000"],
                                            [25, "1.64320"],
                                            [100, "1.48400"]
                                        ]
                                    }
                                }
                            ],
                            "product_url": "https://octopart.com/click/track?ak=a8cfd5a0&sig=09ff747&sid=459&ppid=77762028&vpid=408719850&ct=offers",  # noqa
                            "seller": {
                                "__class__": "Seller",
                                "display_flag": "US",
                                "has_ecommerce": True,
                                "homepage_url": "http://www.digikey.com",
                                "id": "459",
                                "name": "Digi-Key",
                                "uid": "2c3be9310496fffc"
                            },
                            "sku": "ATTINY2313-20SU-ND"
                        }
                    ]
                }
            ]
        }

        with octopart_mock_response(response_body) as response:
            dict_ = self.client.match(
                [{'q': 'ATTINY2313-20SU'}], hide=['offers'])
            [result] = dict_['results']
            [item] = result['items']
            assert item['mpn'] == "ATTINY2313-20SU"
            called_url = request_url_from_request_mock(response)
            assert '/parts/match' in called_url
            assert 'hide%5B%5D=offers' in called_url

    def test_show_directive(self):
        with octopart_mock_response() as response:
            self.client.match([{'q': 'FAKE_MPN'}], show=['offers'])
            called_url = request_url_from_request_mock(response)
            assert '/parts/match' in called_url
            assert 'show%5B%5D=offers' in called_url

    def test_include_directive(self):
        with octopart_mock_response() as response:
            self.client.match([{'q': 'FAKE_MPN'}], includes=['cad_models'])
            called_url = request_url_from_request_mock(response)
            assert '/parts/match' in called_url
            assert 'include%5B%5D=cad_models' in called_url

    def test_no_directives(self):
        with octopart_mock_response() as response:
            self.client.match([{'q': 'FAKE_MPN'}])
            called_url = request_url_from_request_mock(response)
            assert '/parts/match' in called_url
            assert 'hide%5B%5D=' not in called_url
            assert 'show%5B%5D=' not in called_url
            assert 'include%5B%5D=' not in called_url
            assert 'exact_only=' not in called_url

    def test_complete_example(self):
        with octopart_mock_response() as response:
            self.client.match([
                {'mpn': 'MPN1', 'brand': 'Brand 1'},
                {'mpn_or_sku': 'MPN-or#SKU2'},
            ], exact_only=True, show=['brand.name'], includes=['imagesets'])
            called_url = request_url_from_request_mock(response)

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
        with pytest.raises(OctopartError):
            self.client.search([{'query': ["not", "a", "string"]}])
        # the exception should prevent any queries from being made
        assert not mock_get.called

    def test_hide_directive(self):
        response_body = {
            "__class__": "SearchResponse",
            "results": [
                {
                    "__class__": "SearchResult",
                    "item": {
                        "__class__": "Part",
                        "brand": {
                            "__class__": "Brand",
                            "homepage_url": "http://www.ohmite.com/",
                            "name": "Ohmite",
                            "uid": "574996437b3e808e"
                        },
                        "manufacturer": {
                            "__class__": "Manufacturer",
                            "homepage_url": "http://www.ohmite.com/",
                            "name": "Ohmite",
                            "uid": "5da998a375de8e6e"
                        },
                        "mpn": "D25K10KE",
                        "octopart_url": "https://octopart.com/d25k10ke-ohmite-150892",  # noqa
                        "redirected_uids": [],
                        "uid": "3cc3f5cb54c9e304"
                    },
                }
            ]
        }

        with octopart_mock_response(response_body) as response:
            dict_ = self.client.search(
                query='resistor 10kohm 10%', hide=['offers'])
            [result] = dict_['results']
            assert result['item']['mpn'] == "D25K10KE"
            called_url = request_url_from_request_mock(response)
            assert '/parts/search' in called_url
            assert 'hide%5B%5D=offers' in called_url

    def test_show_directive(self):
        response_body = {
            "__class__": "SearchResponse",
            "results": [
                {
                    "__class__": "SearchResult",
                    "item": {
                        "offers": [
                            {
                                "__class__": "PartOffer",
                                "eligible_region": "US",
                                "factory_lead_days": None,
                                "factory_order_multiple": None,
                                "in_stock_quantity": 29,
                                "is_authorized": True,
                                "is_realtime": False,
                                "last_updated": "2018-04-30T17:53:11Z",
                                "moq": 1,
                                "multipack_quantity": "1",
                                "octopart_rfq_url": None,
                                "on_order_eta": None,
                                "on_order_quantity": None,
                                "order_multiple": None,
                                "packaging": None,
                                "prices": {
                                    "USD": [
                                        [1, "13.65000"],
                                        [10, "12.40000"],
                                        [25, "11.17000"],
                                        [50, "10.56000"],
                                        [100, "10.44000"],
                                        [250, "8.92000"],
                                        [500, "8.75000"]
                                    ]
                                },
                                "product_url": "https://octopart.com/click/track?ak=a8cfd5a0&sig=08c4b0d&sid=2402&ppid=150892&vpid=3009946&ct=offers",  # noqa
                                "seller": {
                                    "__class__": "Seller",
                                    "display_flag": "US",
                                    "has_ecommerce": True,
                                    "homepage_url": "http://www.newark.com",
                                    "id": "2402",
                                    "name": "Newark",
                                    "uid": "d294179ef2900153"
                                },
                                "sku": "64K4273"
                            }
                        ]
                    }
                }
            ]
        }

        with octopart_mock_response(response_body) as response:
            dict_ = self.client.search(
                query='resistor 10kohm 10%', show=['offers'])
            [result] = dict_['results']
            [offer] = result['item']['offers']
            assert offer['in_stock_quantity'] == 29
            called_url = request_url_from_request_mock(response)
            assert '/parts/search' in called_url
            assert 'show%5B%5D=offers' in called_url

    def test_include_directive(self):
        with octopart_mock_response() as response:
            self.client.search(
                query='resistor 10kohm 10%', includes=['cad_models'])
            called_url = request_url_from_request_mock(response)
            assert '/parts/search' in called_url
            assert 'include%5B%5D=cad_models' in called_url

    def test_no_directives(self):
        with octopart_mock_response() as response:
            self.client.search(query='resistor 10kohm 10%')
            called_url = request_url_from_request_mock(response)
            assert '/parts/search' in called_url
            assert 'hide%5B%5D=' not in called_url
            assert 'show%5B%5D=' not in called_url
            assert 'include%5B%5D=' not in called_url

    def test_complete_example(self):
        with octopart_mock_response() as response:
            self.client.search(
                query='resistor 10kohm 10%',
                show=['brand.name'],
                includes=['imagesets'],
                start=50,
                limit=50,
                sortby=[('score', 'desc')],
            )
            called_url = request_url_from_request_mock(response)
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
        response_body = {
              "__class__": "Brand",
              "homepage_url": "http://www.newark.com",
              "name": "Newark",
              "uid": "98785972bc7c4fbf"
            }

        with octopart_mock_response(response_body) as response:
            brand = self.client.get_brand('98785972bc7c4fbf')
            assert brand['uid'] == '98785972bc7c4fbf'
            called_url = request_url_from_request_mock(response)
            assert '/brands/98785972bc7c4fbf' in called_url

    def test_search_brand(self):
        response_body = {
            "__class__": "SearchResponse",
            "results": [
                {
                    "__class__": "SearchResult",
                    "item": {
                        "__class__": "Brand",
                        "homepage_url": "http://www.newark.com",
                        "name": "Newark",
                        "uid": "98785972bc7c4fbf"
                    }
                }
            ]
        }

        with octopart_mock_response(response_body) as response:
            response_data = self.client.search_brand('Newark')
            [result] = response_data['results']
            assert result['item']['name'] == 'Newark'
            called_url = request_url_from_request_mock(response)
            assert '/brands/search' in called_url
            assert 'q=Newark' in called_url


class CategorySearchTests(TestCase):
    """Tests for the client's search_category() and get_category() methods"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    def test_get_category(self):
        response_body = {
            "__class__": "Category",
            "ancestor_names": [
                "Electronic Parts",
                "Passive Components"
            ],
            "ancestor_uids": [
                "8a1e4714bb3951d9",
                "7542b8484461ae85"
            ],
            "children_uids": [
                "db8a1680eaa4004d",
                "eb282622da0730ef",
                "e2992f93d3b3395e",
                "e7ca2ac0de173c0d",
                "f6473b4dcf9d2d80",
                "1db9d0b32462c67e",
                "e0b52dbfd96d3b72",
                "d820152ae1f903e7",
                "f0433d49c9e52b84"
            ],
            "name": "Capacitors",
            "num_parts": 1395137,
            "parent_uid": "7542b8484461ae85",
            "uid": "f8883582c9a8234f"
        }

        with octopart_mock_response(response_body) as response:
            dict_ = self.client.get_category('f8883582c9a8234f')
            assert dict_['name'] == 'Capacitors'
            called_url = request_url_from_request_mock(response)
            assert '/categories/f8883582c9a8234f' in called_url

    def test_search_category(self):
        response_body = {
            "__class__": "SearchResponse",
            "results": [
                {
                    "__class__": "SearchResult",
                    "item": {
                        "__class__": "Category",
                        "ancestor_names": [
                            "Electronic Parts",
                            "Passive Components"
                        ],
                        "ancestor_uids": [
                            "8a1e4714bb3951d9",
                            "7542b8484461ae85"
                        ],
                        "children_uids": [
                            "db8a1680eaa4004d",
                            "eb282622da0730ef",
                            "e2992f93d3b3395e",
                            "e7ca2ac0de173c0d",
                            "f6473b4dcf9d2d80",
                            "1db9d0b32462c67e",
                            "e0b52dbfd96d3b72",
                            "d820152ae1f903e7",
                            "f0433d49c9e52b84"
                        ],
                        "name": "Capacitors",
                        "num_parts": 1395137,
                        "parent_uid": "7542b8484461ae85",
                        "uid": "f8883582c9a8234f"
                    }
                }
            ]
        }

        with octopart_mock_response(response_body) as response:
            dict_ = self.client.search_category('Capacitors')
            [result] = dict_['results']
            assert result['item']['name'] == 'Capacitors'
            called_url = request_url_from_request_mock(response)
            assert '/categories/search' in called_url
            assert 'q=Capacitors' in called_url


class SellerSearchTests(TestCase):
    """Tests for the client's search_seller() and get_seller() methods"""
    def setUp(self):
        self.client = OctopartClient(api_key='TEST_TOKEN')

    def test_get_seller(self):
        with octopart_mock_response() as response:
            self.client.get_seller('seller_uuid')
            called_url = request_url_from_request_mock(response)
            assert '/sellers/seller_uuid' in called_url

    def test_search_seller(self):
        response_body = {
            "__class__": "SearchResponse",
            "results": [
                {
                    "__class__": "SearchResult",
                    "item": {
                        "__class__": "Seller",
                        "display_flag": "US",
                        "has_ecommerce": True,
                        "homepage_url": "http://www.mouser.com",
                        "id": "2401",
                        "name": "Mouser",
                        "uid": "a5e060ea85e77627"
                    }
                }
            ]
        }

        with octopart_mock_response(response_body) as response:
            dict_ = self.client.search_seller('Mouser')
            [result] = dict_['results']
            assert result['item']['name'] == 'Mouser'
            called_url = request_url_from_request_mock(response)
            assert '/sellers/search' in called_url
            assert 'q=Mouser' in called_url

    def test_search_seller_with_sortby(self):
        response_body = {
            "__class__": "SearchResponse",
            "results": [
                {
                    "__class__": "SearchResult",
                    "item": {
                        "__class__": "Seller",
                        "display_flag": "US",
                        "has_ecommerce": True,
                        "homepage_url": "http://www.mouser.com",
                        "id": "2401",
                        "name": "Mouser",
                        "uid": "a5e060ea85e77627"
                    }
                }
            ]
        }

        with octopart_mock_response(response_body) as response:
            dict_ = self.client.search_seller(
                'Mouser', sortby=[('name', 'asc')])
            assert 'results' in dict_
            called_url = request_url_from_request_mock(response)
            assert '/sellers/search' in called_url
            assert 'q=Mouser' in called_url
            assert 'sortby=name+asc' in called_url

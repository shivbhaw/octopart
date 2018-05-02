import os
import re
from unittest import TestCase

import responses

from octopart import api, models
from octopart.client import OctopartClient

from . import fixtures
from .utils import octopart_mock_response
from .utils import request_url_from_request_mock


class BrandTests(TestCase):
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

        with octopart_mock_response(response_body):
            brand = api.get_brand('98785972bc7c4fbf')
            assert brand.uid == '98785972bc7c4fbf'

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
            [brand] = api.search_brand('Newark')
            assert brand.name == 'Newark'
            called_url = request_url_from_request_mock(response)
            assert '/brands/search' in called_url
            assert 'q=Newark' in called_url


class PartsTests(TestCase):
    def setUp(self):
        self.old_octopart_key = os.getenv('OCTOPART_API_KEY', "")
        os.environ['OCTOPART_API_KEY'] = 'TEST_KEY'

    def tearDown(self):
        os.environ['OCTOPART_API_KEY'] = self.old_octopart_key

    @responses.activate
    def test_parts_match(self):
        """Tests that `match` returns part matches"""
        # Mock out all calls to match endpoint.
        url_regex = re.compile(r'https://octopart\.com/api/v3/parts/match.*')
        responses.add(
            responses.GET,
            url_regex,
            json=fixtures.parts_match_response,
            status=200,
            content_type='application/json'
        )

        results = api.match(['RUM001L02T2CL'])

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, models.PartsMatchResult)

        assert len(result.parts) == 1
        part = result.parts[0]
        assert isinstance(part, models.Part)
        assert part.mpn == 'RUM001L02T2CL'
        assert part.manufacturer == 'Rohm'

        assert len(part.offers) == 19
        offer = part.offers[0]
        assert isinstance(offer, models.PartOffer)

        assert offer.prices == {
            'USD': {
                8000: 0.05250,
                16000: 0.04463,
                24000: 0.04200,
                56000: 0.03938
            }
        }

    @responses.activate
    def test_parts_match_extra_fields(self):
        """
        Tests that `match` returns matches with additional part-related data.
        """
        # Mock out all calls to match endpoint.
        url_regex = re.compile(r'https://octopart\.com/api/v3/parts/match.*')
        responses.add(
            responses.GET,
            url_regex,
            json=fixtures.parts_match_extra_fields_response,
            status=200,
            content_type='application/json'
        )

        results = api.match(
            ['RUM001L02T2CL'],
            specs=True,
            imagesets=True,
            descriptions=True)

        assert len(results) == 1
        result = results[0]
        assert len(result.parts) == 1
        part = result.parts[0]
        assert part.mpn == 'RUM001L02T2CL'

        assert part.specs['packaging'].value == 'Tape & Reel (TR)'
        assert part.specs['lead_free_status'].value == 'Lead Free'
        assert part.specs['rohs_status'].value == 'Compliant'
        assert part.specs['mounting_style'].value == 'Surface Mount'
        assert part.specs['polarity'].value == 'N-Channel'

        assert len(part.imagesets) == 3
        imageset = part.imagesets[0]
        assert imageset.image_urls == {
            'medium_image': 'https://sigma.octopart.com/67745388/image/Rohm-RUM001L02T2CL.jpg',  # noqa
            'small_image': 'https://sigma.octopart.com/66829790/image/Rohm-RUM001L02T2CL.jpg',  # noqa
            'swatch_image': 'https://sigma.octopart.com/23299222/image/Rohm-RUM001L02T2CL.jpg'  # noqa
        }

        assert len(part.descriptions) == 9
        assert part.descriptions == [
            'MOSFET, N-CH, 20V, 0.1A, VMT',
            'Trans MOSFET N-CH 20V 0.1A 3-Pin VMT T/R',
            'MOSFET N-channel 20V 100mA SOT723',
            'MOSFET N-CH 20V 0.1A VMT3',
            'Trans MOSFET N-CH 20V 0.1A 3-Pin VMT T/R',
            'MOSFET, N-CH, 20V, 0.1A, VMT',
            'Trans MOSFET N-CH 20V 0.1A 3-Pin VMT T/R',
            'Trans MOSFET N-CH 20V 0.1A 3-Pin VMT T/R',
            'RUM001L02 Series 20 V 3.5 Ohm 100 mA N-Ch. Small Signal Mosfet - SOT-723 (VMT3)'  # noqa
        ]

    @responses.activate
    def test_parts_search(self):
        """
        Tests that `search` returns parts that match the search keyword.
        """
        # Mock out all calls to search endpoint.
        url_regex = re.compile(r'https://octopart\.com/api/v3/parts/search.*')
        responses.add(
            responses.GET,
            url_regex,
            json=fixtures.parts_search_response,
            status=200,
            content_type='application/json'
        )

        result = api.search("DISTANCE METER, LASER, 100M")
        assert isinstance(result, models.PartsSearchResult)

        assert len(result.parts) == 8
        part = result.parts[0]
        assert isinstance(part, models.Part)
        assert part.mpn == 'FLUKE-424D'
        assert part.manufacturer == 'Fluke'

        assert len(part.offers) == 19
        offer = part.offers[0]
        assert isinstance(offer, models.PartOffer)
        assert offer.prices == {
            'USD': {1: 424.99000}
        }

    @responses.activate
    def test_match_parts_by_seller(self):
        """
        Tests that including specific sellers in `match` call
        passes those values to Octopart.
        """
        # Mock out all calls to match endpoint.
        url_regex = re.compile(r'https://octopart\.com/api/v3/parts/match.*')
        responses.add(
            responses.GET,
            url_regex,
            json=fixtures.parts_match_multiple_sellers_response,
            status=200,
            content_type='application/json'
        )

        results = api.match(['RUM001L02T2CL'], sellers=['Digi-Key', 'Mouser'])

        assert len(results) == 2
        for result in results:
            assert isinstance(result, models.PartsMatchResult)
            for part in result.parts:
                assert part.mpn == 'RUM001L02T2CL'
                sellers = [offer.seller for offer in part.offers]
                # NOTE: shouldn't assert that other sellers are absent from
                # this list, since they actually can be present in responses
                # that include the `sellers` field in queries.
                assert 'Digi-Key' in sellers
                assert 'Mouser' in sellers

    def test_match_include_directives(self):
        with octopart_mock_response() as rsps:
            api.match(
                ['MPN1', 'MPN2'],
                include_imagesets=True,
                include_cad_models=True
            )
            called_url = request_url_from_request_mock(rsps)

            # %22mpn%22%3A+%22MPN1%22 is "mpn": "MPN1"
            assert '%22mpn_or_sku%22%3A+%22MPN1%22' in called_url
            # %22mpn%22%3A+%22MPN2%22 is "mpn": "MPN2"
            assert '%22mpn_or_sku%22%3A+%22MPN2%22' in called_url
            assert 'include%5B%5D=imagesets' in called_url  # %5B%5D is []
            assert 'include%5B%5D=cad_models' in called_url


class CategoryTests(TestCase):
    def setUp(self):
        self.old_octopart_key = os.getenv('OCTOPART_API_KEY', "")
        os.environ['OCTOPART_API_KEY'] = 'TEST_KEY'

    def tearDown(self):
        os.environ['OCTOPART_API_KEY'] = self.old_octopart_key

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
                            "917d5c77a0544aba",
                            "cda900a3fc9b166e",
                            "01fbccf130c0da3c",
                            "6939a433502db2fe",
                            "a2f46ffe9b377933",
                            "c841054bf1801386",
                            "91ee5ce4a8204a29"
                        ],
                        "name": "Resistors",
                        "num_parts": 1998389,
                        "parent_uid": "7542b8484461ae85",
                        "uid": "5c6a91606d4187ad"
                    }
                }
            ]
        }

        with octopart_mock_response(response_body) as rsps:
            [category] = api.search_category(query='Resistors')
            assert category.uid == '5c6a91606d4187ad'

            called_url = request_url_from_request_mock(rsps)
            assert 'q=Resistors' in called_url

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
                "917d5c77a0544aba",
                "cda900a3fc9b166e",
                "01fbccf130c0da3c",
                "6939a433502db2fe",
                "a2f46ffe9b377933",
                "c841054bf1801386",
                "91ee5ce4a8204a29"
            ],
            "name": "Resistors",
            "num_parts": 1998389,
            "parent_uid": "7542b8484461ae85",
            "uid": "5c6a91606d4187ad"
        }

        with octopart_mock_response(response_body) as rsps:
            category = api.get_category('5c6a91606d4187ad')
            assert category.name == 'Resistors'

            called_url = request_url_from_request_mock(rsps)
            assert '5c6a91606d4187ad' in called_url


class SellerTests(TestCase):
    def setUp(self):
        self.old_octopart_key = os.getenv('OCTOPART_API_KEY', "")
        os.environ['OCTOPART_API_KEY'] = 'TEST_KEY'

    def tearDown(self):
        os.environ['OCTOPART_API_KEY'] = self.old_octopart_key

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
                        "homepage_url": "http://www.digikey.com",
                        "id": "459",
                        "name": "Digi-Key",
                        "uid": "2c3be9310496fffc"
                    }
                }
            ]
        }

        with octopart_mock_response(response_body) as rsps:
            [seller] = api.search_seller(query='Digi-Key')
            assert seller.uid == '2c3be9310496fffc'

            called_url = request_url_from_request_mock(rsps)
            assert 'q=Digi-Key' in called_url

    def test_get_seller(self):
        response_body = {
            "__class__": "Seller",
            "display_flag": "US",
            "has_ecommerce": True,
            "homepage_url": "http://www.digikey.com",
            "id": "459",
            "name": "Digi-Key",
            "uid": "2c3be9310496fffc"
        }

        with octopart_mock_response(response_body) as rsps:
            seller = api.get_seller('2c3be9310496fffc')
            assert seller.name == 'Digi-Key'

            called_url = request_url_from_request_mock(rsps)
            assert '2c3be9310496fffc' in called_url

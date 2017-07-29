import os
import re
import unittest

import responses

from octopart import api
from octopart.models import PartsMatchResult
from octopart.models import PartsSearchResult
from octopart.models import Part
from octopart.models import PartOffer

from . import fixtures
from .utils import octopart_mock_response
from .utils import request_url_from_request_mock


class APITests(unittest.TestCase):
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

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertTrue(isinstance(result, PartsMatchResult))

        self.assertEqual(len(result.parts), 1)
        part = result.parts[0]
        self.assertTrue(isinstance(part, Part))
        self.assertEqual(part.mpn, 'RUM001L02T2CL')
        self.assertEqual(part.manufacturer, 'Rohm')

        self.assertEqual(len(part.offers), 19)
        offer = part.offers[0]
        self.assertTrue(isinstance(offer, PartOffer))

        self.assertEqual(offer.prices, {
            'USD': {
                8000: 0.05250,
                16000: 0.04463,
                24000: 0.04200,
                56000: 0.03938
            }
        })

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

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(len(result.parts), 1)
        part = result.parts[0]
        self.assertEqual(part.mpn, 'RUM001L02T2CL')

        self.assertEqual(part.specs.to_dict(), {
            'packaging': 'Tape & Reel (TR)',
            'lead_free_status': 'Lead Free',
            'rohs_status': 'Compliant',
            'mounting_style': 'Surface Mount',
            'polarity': 'N-Channel'
        })

        self.assertEqual(len(part.imagesets), 3)
        imageset = part.imagesets[0]
        self.assertEqual(imageset.image_urls, {
            'medium_image': 'https://sigma.octopart.com/67745388/image/Rohm-RUM001L02T2CL.jpg',  # noqa
            'small_image': 'https://sigma.octopart.com/66829790/image/Rohm-RUM001L02T2CL.jpg',  # noqa
            'swatch_image': 'https://sigma.octopart.com/23299222/image/Rohm-RUM001L02T2CL.jpg'  # noqa
        })

        self.assertEqual(len(part.descriptions), 9)
        self.assertEqual(part.descriptions, [
            'MOSFET, N-CH, 20V, 0.1A, VMT',
            'Trans MOSFET N-CH 20V 0.1A 3-Pin VMT T/R',
            'MOSFET N-channel 20V 100mA SOT723',
            'MOSFET N-CH 20V 0.1A VMT3',
            'Trans MOSFET N-CH 20V 0.1A 3-Pin VMT T/R',
            'MOSFET, N-CH, 20V, 0.1A, VMT',
            'Trans MOSFET N-CH 20V 0.1A 3-Pin VMT T/R',
            'Trans MOSFET N-CH 20V 0.1A 3-Pin VMT T/R',
            'RUM001L02 Series 20 V 3.5 Ohm 100 mA N-Ch. Small Signal Mosfet - SOT-723 (VMT3)'  # noqa
        ])

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
        self.assertTrue(isinstance(result, PartsSearchResult))

        self.assertEqual(len(result.parts), 8)
        part = result.parts[0]
        self.assertTrue(isinstance(part, Part))
        self.assertEqual(part.mpn, 'FLUKE-424D')
        self.assertEqual(part.manufacturer, 'Fluke')

        self.assertEqual(len(part.offers), 19)
        offer = part.offers[0]
        self.assertTrue(isinstance(offer, PartOffer))
        self.assertEqual(offer.prices, {
            'USD': {1: 424.99000}
        })

    @responses.activate
    def test_match_sellers(self):
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

        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(isinstance(result, PartsMatchResult))
            for part in result.parts:
                self.assertEqual(part.mpn, 'RUM001L02T2CL')
                sellers = [offer.seller for offer in part.offers]
                # NOTE: shouldn't assert that other sellers are absent from
                # this list, since they actually can be present in responses
                # that include the `sellers` field in queries.
                self.assertIn('Digi-Key', sellers)
                self.assertIn('Mouser', sellers)

    def test_deprecated_arguments(self):
        """Using datasheets=True inst of include_datasheets works but warns"""
        with octopart_mock_response() as rsps:
            with self.assertWarns(DeprecationWarning):
                api.match(['FAKE_MPN'], datasheets=True)
            called_url = request_url_from_request_mock(rsps)
            assert 'include%5B%5D=datasheets' in called_url  # %5B%5D is []

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

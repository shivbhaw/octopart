import os
import unittest

from octopart.client import OctopartClient
from octopart.exceptions import OctopartError
# from octopart.models import PartsMatchResult
# from octopart.models import Part
# from octopart.models import PartOffer


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.old_octopart_key = os.getenv('OCTOPART_API_KEY', "")
        os.environ['OCTOPART_API_KEY'] = ''

    def tearDown(self):
        os.environ['OCTOPART_API_KEY'] = self.old_octopart_key

    def test_missing_api_token(self):
        with self.assertRaises(ValueError):
            OctopartClient()

    def test_malformed_query(self):
        with self.assertRaises(OctopartError):
            # TODO: get actual test account.
            client = OctopartClient(api_key='TEST_TOKEN')
            client.match({'q': ["not", "a", "string"]})

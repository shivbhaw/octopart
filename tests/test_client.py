import os
import unittest

from octopart.client import OctopartClient
from octopart.exceptions import OctopartError


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.old_octopart_key = os.getenv('OCTOPART_API_KEY', "")
        os.environ['OCTOPART_API_KEY'] = ''

    def tearDown(self):
        os.environ['OCTOPART_API_KEY'] = self.old_octopart_key

    def test_missing_api_token(self):
        with self.assertRaises(ValueError):
            OctopartClient()

    def test_malformed_match_query(self):
        client = OctopartClient(api_key='TEST_TOKEN')
        with self.assertRaises(OctopartError):
            # TODO: get actual test account.
            client.match([{'q': ["not", "a", "string"]}])

    def test_too_many_match_queries(self):
        client = OctopartClient(api_key='TEST_TOKEN')
        queries = [{'q': 'fake-mpn'}] * 21
        with self.assertRaises(ValueError):
            client.match(queries)

    def test_malformed_search_query(self):
        client = OctopartClient(api_key='TEST_TOKEN')
        with self.assertRaises(OctopartError):
            client.search(["query1", "query2"])

    def test_bad_api_token(self):
        client = OctopartClient(api_key='BAD_TOKEN')
        with self.assertRaises(OctopartError):
            client.match([{'q': 'RUM001L02T2CL'}])

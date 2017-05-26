import unittest

from octopart import utils


class ClientTests(unittest.TestCase):
    def test_chunk_queries(self):
        """
        Tests splitting list of query dicts into smaller chunks.
        """
        queries = [1] * 100
        chunked = utils.chunk_queries(queries)
        self.assertEqual(chunked, [
            [1] * 20,
            [1] * 20,
            [1] * 20,
            [1] * 20,
            [1] * 20
        ])

        # Test odd number of queries.
        queries = [1] * 99
        chunked = utils.chunk_queries(queries)
        self.assertEqual(chunked, [
            [1] * 20,
            [1] * 20,
            [1] * 20,
            [1] * 20,
            [1] * 19
        ])

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


class SortbyParamTests(unittest.TestCase):
    def test_empty_sortby(self):
        self.assertEqual(utils.sortby_param_str_from_list(), '')

    def test_single_sortby(self):
        utils.sortby_param_str_from_list([('val', 'desc')]) == 'val desc'

    def test_multiple_sortby(self):
        utils.sortby_param_str_from_list(
            [('val', 'desc'), ('val2', 'asc')]) == 'val desc,val2 asc'

    def test_not_a_list(self):
        with self.assertRaises(TypeError):
            utils.sortby_param_str_from_list(123)

    def test_bad_tuple(self):
        with self.assertRaises(TypeError):
            utils.sortby_param_str_from_list([('val', )])
        with self.assertRaises(TypeError):
            utils.sortby_param_str_from_list([('val', 'abc', 'def')])

    def test_invalid_order(self):
        with self.assertRaises(TypeError):
            utils.sortby_param_str_from_list([('val', 'abc')])

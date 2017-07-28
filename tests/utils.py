"""Utility functions for testing, _not_ tests for utilities"""


from contextlib import contextmanager
import re

import responses


@contextmanager
def octopart_mock_response():
    """Boilerplate for mocking all Octopart API URLs with an empty response"""
    with responses.RequestsMock() as rsps:
        rsps.add(
            responses.GET,
            re.compile(r'https://octopart\.com/api/v3/.*'),
            body='{"results": []}',
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

import logging

logger = logging.getLogger(__name__)


def setupLogger(logger):
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


setupLogger(logger)


from .api import (  # noqa
    match, search, get_seller, search_seller,
    get_category, search_category, get_brand, search_brand)

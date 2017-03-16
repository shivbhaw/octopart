"""
Types that wrap responses from the Octopart API
and make various attributes easier to access.
"""

from schematics.exceptions import ConversionError, DataError, ValidationError
from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import DictType


class BaseModel(Model):
    @classmethod
    def errors(cls, dict_):
        """
        Wraps `schematics` validate method to return an error list instead of
        having to catch an exception in the caller.

        Returns:
            list of validation errors, or None.
        """
        try:
            cls(dict_).validate()
            return None
        except (DataError, ValidationError) as err:
            return err.messages

    @classmethod
    def errors_list(cls, list_):
        """
        Return any validation errors in list of dicts.

        Args:
            list_ (list): dicts to be validated.

        Returns:
            list of errors, if any, otherwise None.
        """
        try:
            errors = [cls(dict_).errors for dict_ in list_]
            if any(errors):
                return filter(None, errors)
            return None
        except (ConversionError, DataError) as err:
            return err.messages

    @classmethod
    def is_valid(cls, dict_):
        return not cls.errors(dict_)

    @classmethod
    def is_valid_list(cls, list_):
        try:
            return all([cls(dict_).is_valid for dict_ in list_])
        except (ConversionError, DataError):
            return False


class PartsMatchQuery(BaseModel):
    """
    Query format sent to the 'parts/match' endpoint.

    For details, see:
        https://octopart.com/api/docs/v3/rest-api#response-schemas-partsmatchquery
    """
    # Free-form keyword query
    q = StringType(default="")
    # MPN search filter
    mpn = StringType()
    # Brand search filter
    brand = StringType()
    # SKU search filter
    sku = StringType()
    # Seller search filter
    seller = StringType()
    # MPN or SKU search filter
    mpn_or_sku = StringType()
    # Ordinal position of first returned item
    start = IntType(default=0)
    # Maximum number of items to return
    limit = IntType(default=3)
    # Arbitrary string for identifying results
    reference = StringType()


class PartsSearchQuery(BaseModel):
    # Free-form keyword query
    q = StringType()
    # Ordinal position of first result
    start = IntType(default=0)
    # Maximum number of results to return
    limit = IntType(default=10)
    # Comma-separated string of <field> <value> pairs
    sortby = StringType(default="score desc")
    # {fieldname: value} dict, values are filtered exactly
    filter_fields = DictType(StringType)
    # {fieldname: value} dict, values can be more complex
    # See for details:
    #    https://octopart.com/api/docs/v3/search-tutorial#filter-queries
    filter_queries = DictType(StringType)


class PartsMatchResponse(object):
    def __init__(self, response):
        self._response = response

    @property
    def request(self):
        return self._response['request']

    @property
    def results(self):
        return [
            PartsMatchResult(result) for result in self._response['results']
        ]

    def __repr__(self):
        return '<PartsMatchResponse: %s results>' % len(self.results)


class PartsMatchResult(object):
    def __init__(self, result):
        self._result = result

    @property
    def mpn(self):
        return self._result['reference']

    @property
    def parts(self):
        return [Part(part) for part in self._result['items']]

    def __repr__(self):
        return '<PartsMatchResult: hits=%s, query=%s>' % (
            self._result['hits'],
            self._result['reference'])

    def pretty_print(self):
        print self
        for part in self.parts:
            print '\t%s' % part
            for offer in part.offers:
                print '\t\t%s' % offer


class PartsSearchResult(object):
    def __init__(self, result):
        self._result = result

    @property
    def parts(self):
        return [
            Part(result['item'])
            for result in self._result['results']
        ]

    def __repr__(self):
        return '<PartsSearchResult: hits=%s>' % self._result['hits']

    def pretty_print(self):
        print self
        for part in self.parts:
            print '\t%s' % part
            for offer in part.offers:
                print '\t\t%s' % offer


class Part(object):
    def __init__(self, part):
        self._part = part

    @property
    def uid(self):
        return self._part['uid']

    @property
    def mpn(self):
        return self._part['mpn']

    @property
    def offers(self):
        return [PartOffer(offer) for offer in self._part['offers']]

    @property
    def specs(self):
        _specs = self._part.get('specs')
        if _specs:
            return Specs(_specs)
        return None

    @property
    def imagesets(self):
        _imagesets = self._part.get('imagesets')
        # TODO: make better accessors for different image URLs.
        if _imagesets:
            return [Imageset(imageset) for imageset in _imagesets]
        return None

    @property
    def descriptions(self):
        _descriptions = self._part.get('descriptions')
        if _descriptions:
            return [desc['value'] for desc in _descriptions]
        return None

    @property
    def datasheets(self):
        _datasheets = self._part.get('datasheets')
        if _datasheets:
            return [ds['url'] for ds in _datasheets]
        return None

    @property
    def manufacturer(self):
        return self._part['manufacturer']['name']

    def __repr__(self):
        return '<Part mpn=%s>' % self.mpn


class Specs(object):
    def __init__(self, specs):
        self._specs = specs

    def to_dict(self):
        return {
            key: (
                value['value'][0]
                if len(value['value']) == 1
                else value['value']
            )
            for key, value in self._specs.iteritems()
        }

    def __repr__(self):
        return repr(self.to_dict())


class Imageset(object):
    SWATCH = 'swatch'
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'

    IMAGE_SIZES = [
        '%s_image' % size
        for size in [SWATCH, SMALL, MEDIUM, LARGE]
    ]

    def __init__(self, imageset):
        self._imageset = imageset

    @property
    def image_urls(self):
        return {
            key: image_data['url'] if image_data else None
            for key, image_data in self._imageset.iteritems()
            if key in self.IMAGE_SIZES and image_data is not None
        }

    def image_url(self, size):
        return self.images.get('%s_image' % size)

    def __repr__(self):
        return repr(self.images)


class PartOffer(object):
    def __init__(self, offer):
        self._offer = offer

    @property
    def sku(self):
        return self._offer['sku']

    @property
    def prices(self):
        return {
            currency: dict(values)
            for currency, values in self._offer['prices'].iteritems()
        }

    @property
    def last_updated(self):
        return self._offer['last_updated']

    @property
    def packaging(self):
        return self._offer['packaging']

    @property
    def in_stock_quantity(self):
        return self._offer['in_stock_quantity']

    @property
    def moq(self):
        return self._offer['moq']

    @property
    def product_url(self):
        return self._offer['product_url']

    @property
    def seller(self):
        return self._offer['seller']['name']

    def __repr__(self):
        return '<Offer sku=%s, seller=%s, in_stock=%s>' % (
            self.sku,
            self.seller,
            self._offer['in_stock_quantity'])

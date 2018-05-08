"""
Types that wrap responses from the Octopart API
and make various attributes easier to access.
"""

from schematics.exceptions import ConversionError, DataError, ValidationError
from schematics.models import Model
from schematics.types import BooleanType, IntType, StringType
from schematics.types.compound import DictType, ListType


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
                return [_f for _f in errors if _f]
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
    """Query format sent to the 'parts/match' endpoint

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
    """Query format sent to the 'parts/match' endpoint

    https://octopart.com/api/docs/v3/rest-api#response-schemas-partsmatchquery
    """
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


class PartsMatchResponse():
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


class PartsMatchResult():
    def __init__(self, result):
        self._result = result

    @property
    def mpn(self):
        return self._result['reference']

    @property
    def parts(self):
        return [Part(part) for part in self._result['items']]

    def __repr__(self):
        return '<PartsMatchResult: hits=%s query=%s>' % (
            self._result['hits'],
            self._result['reference'])

    def pretty_print(self):
        print(self)
        for part in self.parts:
            print('\t%s' % part)
            for offer in part.offers:
                print('\t\t%s' % offer)


class PartsSearchResult():
    def __init__(self, result):
        self._result = result

    @property
    def parts(self):
        return [
            Part(result['item'])
            for result in self._result.get('results', [])
        ]

    def __repr__(self):
        return '<PartsSearchResult: hits=%s>' % self._result['hits']

    def pretty_print(self):
        print(self)
        for part in self.parts:
            print('\t%s' % part)
            for offer in part.offers:
                print('\t\t%s' % offer)


class Part():
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
    def category_uids(self):
        return self._part['category_uids']

    @property
    def specs(self):
        _specs = self._part.get('specs')
        if _specs:
            return Specs({
                name: Spec(name, spec)
                for name, spec in _specs.items()
            })
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


class Specs(dict):
    """
    XXX: Copied for backwards-compatibility while we phase out use of `Specs`
    in tempocom.
    """
    def to_dict(self):
        return {name: spec.value for name, spec in self.items()}


class Spec():
    def __init__(self, name, spec):
        self._name = name
        self._spec = spec

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        val = self._spec['value']
        if isinstance(val, list) and len(val) == 1:
            return val[0]
        return val

    @property
    def display_value(self):
        return self._spec['display_value']

    @property
    def min_value(self):
        return self._spec['min_value']

    @property
    def max_value(self):
        return self._spec['max_value']

    @property
    def metadata(self):
        return self._spec['metadata']

    @property
    def attribution(self):
        return self._spec['attribution']

    def __repr__(self):
        return f'<Spec name={self.name} value={self.value}>'


class Imageset():
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
            key: image_data['url']
            for key, image_data in self._imageset.items()
            if key in self.IMAGE_SIZES and image_data is not None
        }

    def image_url(self, size):
        return self.image_urls.get('%s_image' % size)

    def __repr__(self):
        return repr(self.images)


class PartOffer():
    def __init__(self, offer):
        self._offer = offer

    @property
    def sku(self):
        return self._offer['sku']

    @property
    def prices(self):
        return {
            currency: {
                int(quantity): float(price)
                for quantity, price in dict(values).items()
            }
            for currency, values in self._offer['prices'].items()
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
        return '<Offer sku=%s seller=%s in_stock_quantity=%s>' % (
            self.sku,
            self.seller,
            self._offer['in_stock_quantity'])


class Brand():
    def __init__(self, brand):
        self._brand = brand

    @property
    def uid(self):
        return self._brand['uid']

    @property
    def name(self):
        return self._brand['name']

    @property
    def homepage_url(self):
        return self._brand['homepage_url']

    def __repr__(self):
        return '<Brand uid=%s name=%s url=%s>' % (
            self.uid,
            self.name,
            self.homepage_url
        )


UIDType = StringType


class Category(BaseModel):
    """The Category schema of the Octopart API v3

    https://octopart.com/api/docs/v3/rest-api#object-schemas-category
    """
    # 64-bit unique identifier (e.g. "b62d7b27870d6dea")
    uid = UIDType()
    # The category node's name (e.g. "Capacitors")
    name = StringType()
    # 64-bit unique identifier of parent category node
    # (e.g. "ab34663e9a1770f3")
    parent_uid = UIDType()
    # JSON array of children uid's
    # (e.g. ["d9ed14e7e8cc022a", "41398c33764e9afe"])
    children_uids = ListType(UIDType)
    # JSON array of ancestor uid's with parent ordered last
    # (e.g. ["55da98d064fd8e1d", "ab34663e9a1770f3"])
    ancestor_uids = ListType(UIDType)
    # JSON array of ancestor node names
    # (e.g. ["Electronic Parts", "Passive Components"])
    ancestor_names = ListType(StringType)
    # Number of parts categorized in category node (e.g. 1000000)
    num_parts = IntType()
    # Hidden by default (See Include Directives)
    # imagesets = ListType()

    def __repr__(self):
        return '<Category uid=%s name=%s>' % (
            self.uid,
            self.name,
        )


class Seller(BaseModel):
    # 64-bit unique identifier (e.g. "4a258f2f6a2199e2")
    uid = UIDType()
    # The seller's display name (e.g. "Newark")
    name = StringType()
    # The seller's homepage url (e.g. "http://example.com)
    homepage_url = StringType()
    # ISO 3166 alpha-2 country code for display flag (e.g. "US")
    display_flag = StringType(max_length=2, min_length=2)
    # Whether seller has e-commerce (true/false)
    has_ecommerce = BooleanType()

    def __repr__(self):
        return '<Seller uid=%s name=%s>' % (
            self.uid,
            self.name,
        )

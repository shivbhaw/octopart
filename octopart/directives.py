import enum


class IncludeDirectives(str, enum.Enum):
    """Categories of information that can optionally be requested

    These categories may be included in the include[] request parameter to
    request additional information in the response content.

    API docs: https://octopart.com/api/docs/v3/rest-api#include-directives
    """
    short_description = 'short_description'
    datasheets = 'datasheets'
    compliance_documents = 'compliance_documents'
    descriptions = 'descriptions'
    imagesets = 'imagesets'
    specs = 'specs'
    category_uids = 'category_uids'
    external_links = 'external_links'
    reference_designs = 'reference_designs'
    cad_models = 'cad_models'

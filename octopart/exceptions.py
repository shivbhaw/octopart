class OctopartError(Exception):
    pass


class OctopartTypeError(OctopartError, TypeError):
    pass

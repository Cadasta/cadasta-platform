class ESNotAvailableError(Exception):

    def __init__(self):
        super().__init__("Elasticsearch API is not available "
                         "or returns an error")


class NotWgs84EwkbValueError(Exception):

    def __init__(self, value):
        super().__init__("Provided value is not a PostGIS hex EWKB value "
                         "in WGS84 datum: " + value)

import json


class JsonValidationError(BaseException):
    def __init__(self, errors):
        self.errors = errors

    def __str__(self):
        return json.dumps(self.errors)

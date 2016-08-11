class InvalidXMLSubmission(Exception):
    def __init__(self, msg, status=None):
        super().__init__(msg)
        self.status = status

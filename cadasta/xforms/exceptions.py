class XFormOutOfDateError(Exception):
    """Exception raised when user submits an out of date form.
    """
    def __init__(self, msg):
        super().__init__(msg)

class InvalidXLSForm(Exception):
    def __init__(self, errors=[], *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.errors = errors

    def __str__(self):
        return ", ".join(self.errors)

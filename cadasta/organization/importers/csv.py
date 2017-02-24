import csv

from . import base


class CSVImporter(base.Importer):

    def __init__(self, project, path, delimiter=',', quotechar='"'):
        super(CSVImporter, self).__init__(project=project)
        self.path = path
        self.delimiter = delimiter
        self.quotechar = quotechar

    def get_headers(self):
        headers = []
        with open(self.path, 'r', newline='') as csvfile:
            reader = csv.reader(
                csvfile, delimiter=self.delimiter, quotechar=self.quotechar
            )
            head = next(reader)
        headers = [
            h.casefold() for h in head if not h.startswith(('_', 'meta/')) and
            h not in base.EXCLUDE_HEADERS
        ]
        return headers

    def import_data(self, config_dict, **kwargs):
        with open(self.path, 'r', newline='') as csvfile:
            self._import(config_dict, csvfile)

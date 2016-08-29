from django.core.files.uploadhandler import TemporaryFileUploadHandler


class S3FileUploadHandler(TemporaryFileUploadHandler):

    def receive_data_chunk(self, raw_data=None, start=None):
        super(S3FileUploadHandler, self).receive_data_chunk(raw_data, start)

    def file_complete(self, file_size):
        self.file.seek(0)
        self.file.size = file_size
        return self.file

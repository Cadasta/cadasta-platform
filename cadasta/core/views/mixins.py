from django.shortcuts import redirect


class ArchiveMixin:
    def archive(self):
        assert hasattr(self, 'do_archive'), "Please set do_archive attribute"
        self.object = self.get_object()
        self.object.archived = self.do_archive
        self.object.save()

        return redirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return self.archive()

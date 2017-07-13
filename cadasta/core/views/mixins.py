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


class SuperUserCheckMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_su = None

    @property
    def is_superuser(self):
        return self.request.user.is_superuser

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['is_superuser'] = self.is_superuser
        return context


class CacheObjectMixin:
    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = super().get_object()
        return self._object

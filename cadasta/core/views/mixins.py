from django.shortcuts import redirect

from tutelary.models import Role


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
        if self.is_su is None:
            role = Role.objects.filter(name='superuser')
            self.is_su = False
            if len(role) > 0:
                if hasattr(self.request.user, 'assigned_policies'):
                    if role[0] in self.request.user.assigned_policies():
                        self.is_su = True
        return self.is_su

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['is_superuser'] = self.is_superuser
        return context


class CacheObjectMixin:
    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = super().get_object()
        return self._object

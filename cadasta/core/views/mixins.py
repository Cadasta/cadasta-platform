from django.shortcuts import redirect
from django.db.models import Q


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
    @property
    def is_superuser(self):
        return self.request.user.is_superuser

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['is_superuser'] = self.is_superuser
        return context


class AsyncList:
    def build_search_query(self, term):
        raise NotImplementedError(
            "You need to implement the method build_search_query.")

    def get_results(self):
        assert hasattr(self, 'sort_columns'), ("Attribute sort_columns is not "
                                               "defined for the view.")

        query = self.request.GET
        qs = self.get_queryset()

        records_total = qs.count()
        # filter the queryset if a search term was provided
        search_term = query.get('search[value]')

        if search_term:
            search = self.build_search_query(search_term)
            assert isinstance(search, Q), ("Return value of build_search_query"
                                           " must be instance of "
                                           "django.db.models.Q")
            qs = qs.filter(search)
        records_filtered = qs.count()

        # set the ordering for the queryset
        order_col = int(query.get('order[0][column]', 0))
        order_dir = '' if query.get('order[0][dir]', 'asc') == 'asc' else '-'
        qs = qs.order_by(order_dir + self.sort_columns[order_col])

        # Slice the queryset to results for the current page
        offset = int(query.get('start', 0))
        limit = int(query.get('length', 10)) + offset
        qs = qs[offset:limit]

        return qs, records_total, records_filtered


class CacheObjectMixin:
    def get_object(self):
        if not hasattr(self, '_object'):
            self._object = super().get_object()
        return self._object

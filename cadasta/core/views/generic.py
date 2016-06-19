import django.views.generic as base

from .mixins import SuperUserCheckMixin


class TemplateView(SuperUserCheckMixin, base.TemplateView):
    pass


class ListView(SuperUserCheckMixin, base.ListView):
    pass


class DetailView(SuperUserCheckMixin, base.DetailView):
    pass


class CreateView(SuperUserCheckMixin, base.CreateView):
    pass


class UpdateView(SuperUserCheckMixin, base.UpdateView):
    pass


class DeleteView(SuperUserCheckMixin, base.DeleteView):
    pass

from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexPage(TemplateView):
    template_name = 'core/index.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_anonymous():
            return redirect('core:dashboard')

        return super(IndexPage, self).get(request, *args, **kwargs)


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

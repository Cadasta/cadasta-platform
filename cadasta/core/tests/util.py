from django.test import TestCase as DjangoTestCase
from django.http import HttpRequest
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse

from core.tests.factories import PolicyFactory
from accounts.tests.factories import UserFactory


class TestCase(DjangoTestCase):
    def setUp(self):
        PolicyFactory.load_policies()
        self.authorized_user = UserFactory.create()
        self.unauthorized_user = UserFactory.create()

        if hasattr(self, 'set_up_models'):
            self.set_up_models()

        if hasattr(self, 'assign_policies'):
            self.assign_policies()

    def request(self, method='GET', user=AnonymousUser(), url_kwargs=None,
                data={}):
        self.request = HttpRequest()
        setattr(self.request, 'method', method)
        setattr(self.request, 'user', user)

        setattr(self.request, 'session', 'session')
        self.messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', self.messages)

        if method in ['POST', 'PATCH', 'PUT']:
            post_data = {}
            if hasattr(self, 'get_post_data'):
                post_data = self.get_post_data()

            elif hasattr(self, 'post_data'):
                post_data = self.post_data

            post_data.update(data)
            setattr(self.request, method, post_data)

        url_params = self.get_url_kwargs()
        if url_kwargs is not None:
            url_params.update(url_kwargs)

        view = self.view.as_view()
        response = view(self.request, **url_params)

        content = None
        if response.status_code == 200:
            content = response.render().content.decode('utf-8')
            return response, content

        return response

    def expected_content(self, **kwargs):
        context = self.get_template_context()

        for key in kwargs:
            context[key] = kwargs[key]

        return render_to_string(self.template, context, request=self.request)

    @property
    def expected_success_url(self):
        return reverse(self.success_url_name,
                       kwargs=self.get_success_url_kwargs())

    def get_template_context(self):
        return {}

    def get_url_kwargs(self):
        return {}

import pytest
from unittest.mock import Mock
from django.http import HttpRequest
from django.test import TestCase
from django.views.generic import View
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages.api import get_messages
from django.contrib.auth.models import AnonymousUser
from skivvy import ViewTestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase
from ..views import auth


class LoginRequiredTest(ViewTestCase, TestCase):
    def test_raise_permission_denied(self):
        """
        View should raise PermissionDenied if user is not logged in and
        raise_exception equals True.
        """
        class TestView(auth.LoginRequiredMixin, View):
            raise_exception = True

        self.view_class = TestView

        with pytest.raises(PermissionDenied):
            self.request()

    def test_redirect_to_login(self):
        """
        View should redirect to login page if user is not logged in and
        raise_exception is not defined.
        """
        class TestView(auth.LoginRequiredMixin, View):
            pass

        self.view_class = TestView

        response = self.request()
        assert response.status_code == 302
        assert 'account/login' in response.location


class PermissionRequiredTest(UserTestCase, ViewTestCase, TestCase):
    def test_permission_required_not_defined(self):
        """
        If neither permission_required is defined or get_permission_required is
        implemented ImproperlyConfigured must be raised
        """
        class TestView(auth.PermissionRequiredMixin, View):
            pass

        view = TestView()
        with pytest.raises(ImproperlyConfigured):
            view.get_permission_required()

    def test_permission_required_defined(self):
        """
        If permission_required is defined, its value should be returned when
        calling get_permission_required
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

        view = TestView()
        assert view.get_permission_required() == 'some.perm'

    def test_get_permission_required_defined(self):
        """
        If get_permission_required is implemented it has prefenence over
        permission_required.
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_permission_required(self):
                return 'other.perm'

        view = TestView()
        assert view.get_permission_required() == 'other.perm'

    def test_get_perms_not_defined(self):
        """
        Instances of auth.PermissionRequiredMixin must implement get_perms
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ['some.perm', 'other.perm']

        view = TestView()
        with pytest.raises(ImproperlyConfigured):
            view.get_perms()

    def test_has_permission_with_string(self):
        """
        permission_required can be defined as a string
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ('some.perm', )

        view = TestView()
        assert view.has_permission() is True

    def test_has_permission_with_tuple(self):
        """
        permission_required can be defined as a tuple
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ('some.perm', 'other.perm')

            def get_perms(self):
                return ('some.perm', 'other.perm')

        view = TestView()
        assert view.has_permission() is True

    def test_has_permission_with_list(self):
        """
        permission_required can be defined as a list
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ['some.perm', 'other.perm']

            def get_perms(self):
                return ('some.perm', 'other.perm')

        view = TestView()
        assert view.has_permission() is True

    def test_has_no_permission_with_permission_required_method(self):
        """
        has_permssions should use return value of get_permission_required
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ['some.perm']

            def get_permission_required(self):
                return 'other.perm'

        view = TestView()
        assert view.has_permission() is False

    def test_has_permission_with_permission_required_method(self):
        """
        has_permssions should use return value of get_permission_required
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ['other.perm']

            def get_permission_required(self):
                return 'other.perm'

        view = TestView()
        assert view.has_permission() is True

    def test_has_permission_permission_denied(self):
        """
        The permission returned from get_perms does not match the one defined
        in permission_required.
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ('other.perm', )

        view = TestView()
        assert view.has_permission() is False

    def test_has_permission_permission_denied_with_list(self):
        """
        All permissions defined in permission_required must be present in the
        return value of get_perms.
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ['some.perm', 'other.perm']

            def get_perms(self):
                return ('some.perm', 'another.perm')

        view = TestView()
        assert view.has_permission() is False

    def test_has_permission_permission_denied_only_one_perm(self):
        """
        All permissions defined in permission_required must be present in the
        return value of get_perms.
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ['some.perm', 'other.perm']

            def get_perms(self):
                return ('some.perm', )

        view = TestView()
        assert view.has_permission() is False

    def test_has_permission_permission_granted_for_list(self):
        """
        All permissions defined in permission_required must be present in the
        return value of get_perms.
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ['some.perm', 'other.perm']

            def get_perms(self):
                return ('some.perm', 'other.perm', 'third.perm')

        view = TestView()
        assert view.has_permission() is True

    def test_has_permission_permission_denied_for_list(self):
        """
        All permissions defined in permission_required must be present in the
        return value of get_perms.
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ['some.perm', 'other.perm']

            def get_perms(self):
                return ('some.perm', 'third.perm')

        view = TestView()
        assert view.has_permission() is False

    def test_test_with_superuser(self):
        """
        For superuser test_func should always return True even if permission
        would be denied otherwise.
        """
        user = UserFactory.create(is_superuser=True)
        request = Mock()
        request.user = user

        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ['some.perm']

            def get_perms(self):
                return ('other.perm', )

        view = TestView()
        view.request = request
        assert view.test_func() is True

    def test_test_with_standarduser(self):
        """
        For standard users test_func should always return False if permission
        is denied.
        """
        user = UserFactory.create()
        request = Mock()
        request.user = user

        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = ['some.perm']

            def get_perms(self):
                return ('other.perm', )

        view = TestView()
        view.request = request
        assert view.test_func() is False

    def test_raise_permission_denied(self):
        """
        View should raise PermissionDenied if required permissions are not met
        and raise_exception equals True.
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'
            raise_exception = True

            def get_perms(self):
                return ('other.perm', )

        self.view_class = TestView

        user = UserFactory.create()
        referer = '/organizations/abc/projects/123'

        with pytest.raises(PermissionDenied):
            self.request(user=user, request_meta={'HTTP_REFERER': referer})

    def test_login_redirect_to_original_referer(self):
        """
        If permissions were denied the view should redirect to the provided
        referer if the user:
        - was not refered from the login page
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ('other.perm', )

        self.view_class = TestView

        user = UserFactory.create()
        referer = '/organizations/abc/projects/123'

        response = self.request(user=user,
                                request_meta={'HTTP_REFERER': referer})
        assert response.status_code == 302
        assert response.location == referer
        assert ("You don't have permission for this action." in
                response.messages)

    def test_login_redirect_to_project_dashboard(self):
        """
        If permissions were denied the view should redirect to the project
        dashboard if the user:
        - tries to access a project page other than the project dashboard
          (incl. location, party and relationship views)
        - was refered from the login page
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ('other.perm', )

        self.view_class = TestView

        user = UserFactory.create()
        referer = '/account/login/'
        url_kwargs = {'organization': 'abc', 'project': '123'}

        response = self.request(user=user,
                                request_meta={'HTTP_REFERER': referer},
                                url_kwargs=url_kwargs)

        exp_redirect = reverse('organization:project-dashboard',
                               kwargs=url_kwargs)
        assert response.status_code == 302
        assert response.location == exp_redirect
        assert ("You don't have permission for this action." in
                response.messages)

    def test_login_redirect_from_project_dashboard_to_org_dashboard(self):
        """
        If permissions were denied the view should redirect to the organization
        dashboard if the user:
        - tries to access the project dashboard
        - was refered from the login page
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ('other.perm', )
        user = UserFactory.create()

        view = TestView.as_view()

        request = HttpRequest()
        request.META['HTTP_REFERER'] = '/account/login/'
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)

        kwargs = {'organization': 'abc', 'project': '123'}

        def get_full_path():
            return '/organizations/abc/projects/123/'
        setattr(request, 'get_full_path', get_full_path)

        exp_redirect = reverse('organization:dashboard', kwargs={
            'slug': 'abc'})
        response = view(request, **kwargs)
        assert response.status_code == 302
        assert exp_redirect == response['location']
        messages = [str(m) for m in get_messages(request)]
        assert "You don't have permission for this action." in messages

    def test_login_redirect_to_organization_dashboard(self):
        """
        If permissions were denied the view should redirect to the organization
        dashboard if the user:
        - tries to access an organization page other than the organization
          dashboard
        - was refered from the login page
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ('other.perm', )

        self.view_class = TestView

        user = UserFactory.create()
        referer = '/account/login/'
        url_kwargs = {'slug': 'abc'}

        response = self.request(user=user,
                                request_meta={'HTTP_REFERER': referer},
                                url_kwargs=url_kwargs)

        exp_redirect = reverse('organization:dashboard',
                               kwargs=url_kwargs)
        assert response.status_code == 302
        assert response.location == exp_redirect
        assert ("You don't have permission for this action." in
                response.messages)

    def test_login_redirect_from_org_dashboard_to_dashboard(self):
        """
        If permissions were denied the view should redirect to the platform
        dashboard if the user:
        - tries to access the organization dashboard
        - was refered from the login page
        """
        class TestView(auth.PermissionRequiredMixin, View):
            permission_required = 'some.perm'

            def get_perms(self):
                return ('other.perm', )

        user = UserFactory.create()
        view = TestView.as_view()

        request = HttpRequest()
        request.META['HTTP_REFERER'] = '/account/login/'
        setattr(request, 'user', user)
        setattr(request, 'method', 'GET')

        setattr(request, 'session', 'session')
        self.messages = FallbackStorage(request)
        setattr(request, '_messages', self.messages)

        kwargs = {'slug': 'abc'}

        def get_full_path():
            return '/organizations/abc/'
        setattr(request, 'get_full_path', get_full_path)

        exp_redirect = reverse('core:dashboard')
        response = view(request, **kwargs)
        assert response.status_code == 302
        assert exp_redirect == response['location']
        messages = [str(m) for m in get_messages(request)]
        assert "You don't have permission for this action." in messages


class SuperUserRequiredTest(UserTestCase, ViewTestCase, TestCase):
    def test_with_superuser(self):
        """
        For superusers, test_func should return True; the permission is granted
        """
        class TestView(auth.SuperUserRequiredMixin, View):
            pass

        user = UserFactory.create(is_superuser=True)
        request = Mock()
        request.user = user

        view = TestView()
        view.request = request
        assert view.test_func() is True

    def test_with_standard_user(self):
        """
        For standard users, test_func should return False; the permission is
        denied
        """
        class TestView(auth.SuperUserRequiredMixin, View):
            pass

        user = UserFactory.create(is_superuser=False)
        request = Mock()
        request.user = user

        view = TestView()
        view.request = request
        assert view.test_func() is False

    def test_with_anonymous_user(self):
        """
        For anonymous users, test_func should return False; the permission is
        denied
        """
        class TestView(auth.SuperUserRequiredMixin, View):
            pass

        user = AnonymousUser()
        request = Mock()
        request.user = user

        view = TestView()
        view.request = request
        assert view.test_func() is False

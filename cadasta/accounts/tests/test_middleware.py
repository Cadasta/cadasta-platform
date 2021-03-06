from django.test import TestCase
from unittest.mock import patch, Mock
from .. import middleware


class UserLanguageMiddlewareTest(TestCase):

    def setUp(self):
        self.mock_request = Mock()
        self.mock_response = Mock()
        self.LANGUAGE_SESSION_KEY = ''
        self.mock_request.session = {self.LANGUAGE_SESSION_KEY: ''}
        self.ulm = middleware.UserLanguageMiddleware()

    @patch.object(middleware, 'translation')
    def test_process_response_user_not_authenticated(self, mock_translation):
        self.mock_request.user.is_authenticated = False
        res = self.ulm.process_response(self.mock_request, self.mock_response)
        assert 0 == mock_translation.activate.call_count
        assert res is self.mock_response

    @patch.object(middleware, 'translation')
    def test_process_response_with_same_language(self, mock_translation):
        self.mock_request.user.is_authenticated = True
        self.mock_request.user.language = 'en'
        mock_translation.get_language.return_value = 'en'
        res = self.ulm.process_response(self.mock_request, self.mock_response)
        assert 0 == mock_translation.activate.call_count
        assert res is self.mock_response

    @patch.object(middleware, 'translation')
    def test_process_response_activate_user_language(self, mock_translation):
        self.mock_request.user.is_authenticated = True
        self.mock_request.user.language = 'fr'
        mock_translation.get_language.return_value = 'en'
        user_lang = self.mock_request.user.language
        session_lang = self.mock_request.session
        session_lang[self.LANGUAGE_SESSION_KEY] = user_lang
        res = self.ulm.process_response(self.mock_request, self.mock_response)
        assert 1 == mock_translation.activate.call_count
        assert 'fr' == session_lang[self.LANGUAGE_SESSION_KEY]
        assert res is self.mock_response

    @patch.object(middleware, 'translation')
    def test_process_response_wsgi_request(self, mock_translation):
        """
        If Auth middleware isn't reached (eg if we return a redirect to
        an endpoint with an appended slash if a slash is ommited from a
        URL and settings.APPEND_SLASH=True), request will be a
        WSGIRequest that does not contain a user property.
        """
        del self.mock_request.user
        res = self.ulm.process_response(self.mock_request, self.mock_response)
        assert 0 == mock_translation.activate.call_count
        assert res is self.mock_response

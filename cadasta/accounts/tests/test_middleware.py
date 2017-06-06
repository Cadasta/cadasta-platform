from django.test import TestCase
from unittest.mock import patch, Mock
from .. import middleware


class UserLanguageMiddlewareTest(TestCase):

    def setUp(self):
        self.mock_request = Mock()
        self.LANGUAGE_SESSION_KEY = ''
        self.mock_request.session = {self.LANGUAGE_SESSION_KEY: ''}
        self.ulm = middleware.UserLanguageMiddleware()

    @patch.object(middleware, 'translation')
    def test_process_request_user_not_authenticated(self, mock_translation):
        self.mock_request.user.is_authenticated = False
        response = self.ulm.process_request(self.mock_request)
        self.assertEqual(0, mock_translation.activate.call_count)
        self.assertIsNone(response)

    @patch.object(middleware, 'translation')
    def test_process_request_with_same_language(self, mock_translation):
        self.mock_request.user.is_authenticated = True
        self.mock_request.user.language = 'en'
        mock_translation.get_language.return_value = 'en'
        response = self.ulm.process_request(self.mock_request)
        self.assertEqual(0, mock_translation.activate.call_count)
        self.assertIsNone(response)

    @patch.object(middleware, 'translation')
    def test_process_request_activate_user_language(self, mock_translation):
        self.mock_request.user.is_authenticated = True
        self.mock_request.user.language = 'fr'
        mock_translation.get_language.return_value = 'en'
        user_lang = self.mock_request.user.language
        session_lang = self.mock_request.session
        session_lang[self.LANGUAGE_SESSION_KEY] = user_lang
        response = self.ulm.process_request(self.mock_request)
        self.assertEqual(1, mock_translation.activate.call_count)
        self.assertEqual('fr', session_lang[self.LANGUAGE_SESSION_KEY])
        self.assertIsNone(response)

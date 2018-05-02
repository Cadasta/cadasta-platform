from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class UserLanguageMiddleware(MiddlewareMixin):

    def process_response(self, request, response):
        if not hasattr(request, 'user'):
            return response

        if not request.user.is_authenticated:
            return response

        user_language = request.user.language
        current_language = translation.get_language()
        if user_language == current_language:
            return response

        translation.activate(user_language)
        request.session[translation.LANGUAGE_SESSION_KEY] = user_language

        return response

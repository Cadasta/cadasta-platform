from django.utils import translation


class UserLanguageMiddleware(object):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None

        user_language = request.user.language
        current_language = translation.get_language()
        if user_language == current_language:
            return None

        translation.activate(user_language)
        request.session[translation.LANGUAGE_SESSION_KEY] = user_language
        return None

    def process_response(self, request, response):
        if not request.user.is_authenticated:
            return response

        user_language = request.user.language
        current_language = translation.get_language()
        if user_language == current_language:
            return response

        translation.activate(user_language)
        request.session[translation.LANGUAGE_SESSION_KEY] = user_language

        return response

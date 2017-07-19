from allauth.account.auth_backends import AuthenticationBackend as Backend
from django.contrib.auth.backends import ModelBackend
from .models import User
from .validators import phone_validator


class AuthenticationBackend(Backend):
    def _authenticate_by_email(self, **credentials):
        # Even though allauth will pass along `email`, other apps may
        # not respect this setting. For example, when using
        # django-tastypie basic authentication, the login is always
        # passed as `username`.  So let's place nice with other apps
        # and use username as fallback
        email = credentials.get('email', credentials.get('username'))
        try:
            user = User.objects.get(email__iexact=email)
            if (user.check_password(credentials["password"]) and
                    self.user_can_authenticate(user)):
                return user
        except User.DoesNotExist:
            pass

        return None


class PhoneAuthenticationBackend(ModelBackend):
    def authenticate(self, **credentials):
        phone = credentials.get('phone', credentials.get('username'))
        if phone_validator(phone):
            try:
                user = User.objects.get(phone__iexact=phone)
                if user.check_password(credentials["password"]):
                    return user
            except User.DoesNotExist:
                pass
        return None

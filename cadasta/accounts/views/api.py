from django.utils.translation import ugettext as _
from allauth.account.utils import send_email_confirmation

from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework import status

from djoser import views as djoser_views
from djoser import signals
from allauth.account.signals import password_changed

from .. import serializers
from ..utils import send_email_update_notification
from ..exceptions import EmailNotVerifiedError


class AccountUser(djoser_views.UserView):
    serializer_class = serializers.UserSerializer

    def perform_update(self, serializer):
        user = self.get_object()
        old_email = user.email
        new_email = serializer.validated_data.get('email', user.email)

        if user.email != new_email:
            updated = serializer.save(email=old_email)
            updated.email = new_email

            send_email_confirmation(self.request._request, updated)
            send_email_update_notification(old_email)

        else:
            serializer.save()


class AccountRegister(djoser_views.RegistrationView):
    serializer_class = serializers.RegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        signals.user_registered.send(sender=self.__class__, user=user,
                                     request=self.request)

        send_email_confirmation(self.request._request, user)


class AccountLogin(djoser_views.LoginView):
    serializer_class = serializers.AccountLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return self._action(serializer)
        except ValidationError:
            return Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        except EmailNotVerifiedError:
            user = serializer.user
            user.is_active = False
            user.save()

            send_email_confirmation(self.request._request, user)

            return Response(
                data={'detail': _("The email has not been verified.")},
                status=status.HTTP_400_BAD_REQUEST,
            )


class SetPasswordView(djoser_views.SetPasswordView):
    def _action(self, serializer):
        response = super()._action(serializer)
        password_changed.send(sender=self.request.user.__class__,
                              request=self.request._request,
                              user=self.request.user)
        return response

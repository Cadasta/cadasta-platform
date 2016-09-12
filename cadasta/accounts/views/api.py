from django.utils.translation import ugettext as _

from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework import status

from djoser import views as djoser_views
from djoser import utils as djoser_utils
from djoser import serializers as djoser_serializers
from djoser import settings

from .. import serializers
from ..exceptions import EmailNotVerifiedError
from ..token import cadastaTokenGenerator


class AccountUser(djoser_utils.SendEmailViewMixin, djoser_views.UserView):
    token_generator = cadastaTokenGenerator
    subject_template_name = 'accounts/email/change_email_subject.txt'
    plain_body_template_name = 'accounts/email/change_email.txt'
    serializer_class = serializers.UserSerializer

    def get_email_context(self, user):
        context = super(AccountUser, self).get_email_context(user)
        context['url'] = settings.get('ACTIVATION_URL').format(**context)
        return context

    def perform_update(self, serializer):
        old_email = self.get_object().email
        new_email = serializer.validated_data['email']

        user = serializer.save()

        if old_email != new_email:
            self.send_email(**self.get_send_email_kwargs(user))

    def put(self, *args, **kwargs):
        print(self.request.method)
        return super().put(*args, **kwargs)


class AccountRegister(djoser_views.RegistrationView):
    token_generator = cadastaTokenGenerator
    serializer_class = serializers.RegistrationSerializer
    plain_body_template_name = 'accounts/email/activate_email.txt'


class AccountLogin(djoser_utils.SendEmailViewMixin, djoser_views.LoginView):
    serializer_class = serializers.AccountLoginSerializer
    token_generator = cadastaTokenGenerator
    subject_template_name = 'accounts/email/activate_email_subject.txt'
    plain_body_template_name = 'accounts/email/activate_email.txt'

    def get_email_context(self, user):
        context = super(AccountLogin, self).get_email_context(user)
        context['url'] = settings.get('ACTIVATION_URL').format(**context)
        return context

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return self.action(serializer)
        except ValidationError:
            return Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        except EmailNotVerifiedError:
            self.send_email(**self.get_send_email_kwargs(serializer.user))
            return Response(
                data={'detail': _("The email has not been verified.")},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordReset(djoser_views.PasswordResetView):
    plain_body_template_name = 'accounts/email/password_reset.txt'


class AccountVerify(djoser_utils.ActionViewMixin, GenericAPIView):
    serializer_class = djoser_serializers.UidAndTokenSerializer
    permission_classes = (AllowAny, )
    token_generator = cadastaTokenGenerator

    def action(self, serializer):
        serializer.user.email_verified = True
        serializer.user.is_active = True
        serializer.user.save()
        return Response(status=status.HTTP_200_OK)

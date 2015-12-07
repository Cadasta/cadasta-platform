from django.utils.translation import ugettext as _
from django.contrib.auth.tokens import default_token_generator

from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework import status

from djoser import views as djoser_views
from djoser import utils as djoser_utils
from djoser import serializers as djoser_serializers
from djoser import settings

from .serializers import RegistrationSerializer, AccountLoginSerializer
from .exceptions import EmailNotVerifiedError


class AccountUser(djoser_utils.SendEmailViewMixin, djoser_views.UserView):
    token_generator = default_token_generator
    subject_template_name = 'activation_email_subject.txt'
    plain_body_template_name = 'activation_email_body.txt'

    def get_email_context(self, user):
        context = super(AccountUser, self).get_email_context(user)
        context['url'] = settings.get('ACTIVATION_URL').format(**context)
        return context

    def perform_update(self, serializer):
        old_obj = self.get_object()
        new_data_dict = serializer.validated_data

        if old_obj.email != new_data_dict['email']:
            self.send_email(**self.get_send_email_kwargs(self.request.user))

        serializer.save()


class AccountRegister(djoser_views.RegistrationView):
    serializer_class = RegistrationSerializer


class AccountLogin(djoser_utils.SendEmailViewMixin, djoser_views.LoginView):
    serializer_class = AccountLoginSerializer
    token_generator = default_token_generator
    subject_template_name = 'activation_email_subject.txt'
    plain_body_template_name = 'activation_email_body.txt'

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


class AccountVerify(djoser_utils.ActionViewMixin, GenericAPIView):
    serializer_class = djoser_serializers.UidAndTokenSerializer
    permission_classes = (AllowAny, )
    token_generator = default_token_generator

    def action(self, serializer):
        serializer.user.email_verified = True
        serializer.user.is_active = True
        serializer.user.save()
        return Response(status=status.HTTP_200_OK)

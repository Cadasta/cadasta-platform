from allauth.account.utils import send_email_confirmation

from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny

from djoser import views as djoser_views
from djoser import signals
from allauth.account.signals import password_changed

from .. import serializers
from .. import utils
from .. import messages
from ..models import VerificationDevice
from accounts import exceptions


class AccountUser(djoser_views.UserView):
    serializer_class = serializers.UserSerializer

    def perform_update(self, serializer):
        instance = self.get_object()
        current_email, current_phone = instance.email, instance.phone
        new_email = serializer.validated_data.get('email', instance.email)
        new_phone = serializer.validated_data.get('phone', instance.phone)
        user = serializer.save()

        if current_email != new_email:
            instance.emailaddress_set.all().delete()

            if new_email:
                send_email_confirmation(self.request._request, user)
                if current_email:
                    user.email = current_email
                    utils.send_email_update_notification(current_email)

        if current_phone != new_phone:
            instance.verificationdevice_set.all().delete()

            if new_phone:
                device = VerificationDevice.objects.create(
                    user=instance,
                    unverified_phone=new_phone)
                device.generate_challenge()
                if current_phone:
                    user.phone = current_phone
                    utils.send_sms(current_phone, messages.phone_change)

        user.save()


class AccountRegister(djoser_views.RegistrationView):
    serializer_class = serializers.RegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        signals.user_registered.send(sender=self.__class__, user=user,
                                     request=self.request)

        if user.email:
            send_email_confirmation(self.request._request, user)
        if user.phone:
            verification_device = VerificationDevice.objects.create(
                user=user,
                unverified_phone=user.phone)
            verification_device.generate_challenge()


class AccountLogin(djoser_views.LoginView):
    serializer_class = serializers.AccountLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            return self._action(serializer)

        except ValidationError:
            error = serializer.errors

        except exceptions.AccountInactiveError as e:
            user = serializer.user
            user.is_active = False
            user.save()
            error = e.msg

        except exceptions.EmailNotVerifiedError as e:
            user = serializer.user
            error = e.msg
            send_email_confirmation(self.request._request, user)

        except exceptions.PhoneNotVerifiedError as e:
            user = serializer.user
            error = e.msg
            device = user.verificationdevice_set.get(label='phone_verify')
            device.generate_challenge()

        return Response(
            data={'detail': error},
            status=status.HTTP_401_UNAUTHORIZED)


class SetPasswordView(djoser_views.SetPasswordView):

    def _action(self, serializer):
        response = super()._action(serializer)
        password_changed.send(sender=self.request.user.__class__,
                              request=self.request._request,
                              user=self.request.user)
        return response


class ConfirmPhoneView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = serializers.PhoneVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except ValidationError:
            return Response(
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            data={'detail': 'Phone successfully verified.'},
            status=status.HTTP_200_OK)

from allauth.account.utils import send_email_confirmation

from rest_framework.serializers import ValidationError
from rest_framework.response import Response
from rest_framework import status

from djoser import views as djoser_views
from djoser import signals
from allauth.account.signals import password_changed

from .. import serializers
from ..utils import send_email_update_notification
from ..models import VerificationDevice
from accounts import exceptions


class AccountUser(djoser_views.UserView):
    serializer_class = serializers.UserSerializer

    def perform_update(self, serializer):
        instance = self.get_object()
        current_email, current_phone = instance.email, instance.phone
        new_email = serializer.validated_data.get('email', instance.email)
        new_phone = serializer.validated_data.get('phone', instance.phone)

        # user will have email & phone as is provided in data
        user = serializer.save()

        # if email and phone are null in both instance's field and serializer
        # data, then raise a Bad Request error

        if current_email != new_email:
            # if data email and instance's email are not equal
            # then delete all emailaddress instances related to the user
            email_set = instance.emailaddress_set.all()
            if email_set.exists():
                email_set.delete()
            # if data email is not None, send a confirmation email to it
            if new_email:
                send_email_confirmation(self.request._request, user)
                # if instance's email is not None, send update notification
                # to it, and set data email back to current email
                if current_email:
                    send_email_update_notification(current_email)
                    user.email = current_email
            # if data's email is None, set email_verified to False
            else:
                user.email_verified = False

        if current_phone != new_phone:
            # if data phone is not equal to user's phone, then
            # delete all verificationdevice instacnces related to the user
            phone_set = VerificationDevice.objects.filter(user=instance)
            if phone_set.exists():
                phone_set.delete()
            # if data phone is not None
            if new_phone:
                # create a new verificationdevice related to the user with
                # the data phone
                device = VerificationDevice.objects.create(
                    user=instance,
                    unverified_phone=new_phone)
                device.generate_challenge()
                # if instance's phone is not None, set data phone back to
                # instance phone
                if current_phone:
                    user.phone = current_phone
            # if data phone is None, set instance phone_verified to False
            else:
                user.phone_verified = False

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
            error = e.msg

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

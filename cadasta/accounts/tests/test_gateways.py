from django.test import TestCase
from django.conf import settings
# from accounts.gateways.twilio import TwilioGateway
# from accounts.gateways.fake import FakeGateway
from accounts.gateways import TwilioGateway, FakeGateway
from django.test.utils import override_settings
from unittest import mock


class TwilioGatewayTest(TestCase):

    @override_settings(
        TWILIO_ACCOUNT_SID='SID',
        TWILIO_AUTH_TOKEN='TOKEN',
        TWILIO_PHONE_NUMBER_LIST=['+123'])
    @mock.patch('accounts.gateways.Client')
    def test_gateway(self, mock_client):
        twilio = TwilioGateway(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            from_phone_number_list=settings.TWILIO_PHONE_NUMBER_LIST
        )
        mock_client.assert_called_with('SID', 'TOKEN')
        body = 'Testing Twilio SMS gateway!'
        to = '+456'
        twilio.send_sms(to, body)
        mock_client.return_value.messages.create.assert_called_with(
            to=to,
            body=body,
            from_='+123')

    def test_message_sent_successfully(self):
        twiliobj = TwilioGateway(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            from_phone_number_list=['+15005550006', ]
        )
        to = '+919327768250'
        body = 'Test message send successfully'
        message = twiliobj.send_sms(to, body)
        assert message.status == 'queued'
        assert message.sid is not None

    def test_message_send_to_invalid_number(self):
        twiliobj = TwilioGateway(
            account_sid=settings.TWILIO_ACCOUNT_SID,
            auth_token=settings.TWILIO_AUTH_TOKEN,
            from_phone_number_list=['+15005550006', ]
        )
        to = '+15005550001'
        body = 'This is an invalid phone number!'
        message = twiliobj.send_sms(to, body)
        assert message.status == 400


class FakeGatewayTest(TestCase):
    @mock.patch('accounts.gateways.fake_logger')
    def test_gateway(self, mock_logger):
        fake_gateway = FakeGateway()
        to = '+456'
        body = 'Testing Fake SMS gateway!'
        fake_gateway.send_sms(to, body)
        mock_logger.debug.assert_called_with(
            "Message sent to: {phone}. Message: {body}".format(
                phone=to, body=body))

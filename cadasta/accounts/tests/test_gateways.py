from django.test import TestCase
from accounts.gateways import TwilioGateway, FakeGateway
from django.test.utils import override_settings
from unittest import mock


class TwilioGatewayTest(TestCase):

    @override_settings(
        TWILIO_ACCOUNT_SID='SID',
        TWILIO_AUTH_TOKEN='TOKEN',
        TWILIO_TWILIO_PHONE='+123')
    @mock.patch('accounts.gateways.Client')
    def test_gateway(self, mock_client):
        twilio = TwilioGateway()
        mock_client.assert_called_with('SID', 'TOKEN')
        body = 'Testing Twilio SMS gateway!'
        to = '+456'
        twilio.send_sms(to, body)
        mock_client.return_value.messages.create.assert_called_with(
            to=to,
            body=body,
            from_='+123')


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

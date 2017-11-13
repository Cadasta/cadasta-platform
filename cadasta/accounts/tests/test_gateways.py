from django.test import TestCase
from django.conf import settings
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

    def test_gateway_exception(self):
        twilio = TwilioGateway(account_sid='SID',
                               auth_token='TOKEN',
                               from_phone_number_list=['+123'])
        body = 'Testing Twilio SMS gateway!'
        to = '+456'
        response = twilio.send_sms(to, body)
        assert response.status == 404
        assert 'Unable to create record' in response.msg


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
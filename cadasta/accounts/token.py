from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import int_to_base36
from django.utils import six
from django.utils.crypto import salted_hmac


class TokenGenerator(PasswordResetTokenGenerator):
    key_salt = "cadasta.account.tokens.TokenGenerator"

    def _make_token_with_timestamp(self, user, timestamp):
        ts_b36 = int_to_base36(timestamp)
        hash = salted_hmac(
            self.key_salt,
            self._make_hash_value(user, timestamp),
        ).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash)

    def _make_hash_value(self, user, timestamp):
        return (
            six.text_type(user.pk) + user.password +
            six.text_type(user.date_joined) + six.text_type(timestamp)
        )

cadastaTokenGenerator = TokenGenerator()

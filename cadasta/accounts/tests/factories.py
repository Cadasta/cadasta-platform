import factory

from core.tests.factories import ExtendedFactory
from ..models import User


class UserFactory(ExtendedFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "testuser%s" % n)
    email = factory.Sequence(lambda n: "email_%s@example.com" % n)
    password = ''

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', None)
        user = super()._build(model_class, *args, **kwargs)
        if password:
            user.set_password(password)
        return user

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', None)
        user = super()._create(model_class, *args, **kwargs)
        if password:
            user.set_password(password)
            user.save()
        return user

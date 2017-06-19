import factory

from core.tests.factories import ExtendedFactory
from ..models import User


class UserFactory(ExtendedFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: "testuser%s" % n)
    email = factory.Sequence(lambda n: "email_%s@example.com" % n)
    phone = factory.Sequence(lambda n: "+120255501%s" % n)
    password = ''

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop('password', None)
        user = super(UserFactory, cls)._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user

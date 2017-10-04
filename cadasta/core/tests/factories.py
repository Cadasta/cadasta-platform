import os.path
import factory

from tutelary.models import Policy, Role
from accounts import load


class ExtendedFactory(factory.django.DjangoModelFactory):
    @classmethod
    def create_from_kwargs(cls, kwargs_list):
        objs = []
        for kwargs in kwargs_list:
            objs.append(cls.create(**kwargs))
        return objs


class PolicyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Policy

    @classmethod
    def set_directory(cls, dir):
        cls.directory = dir

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        body_file = os.path.join(cls.directory, kwargs.pop('file', None))
        with open(body_file) as body:
            kwargs['body'] = body.read()
            return kwargs

    def load_policies(force=True):
        load.run(force)


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

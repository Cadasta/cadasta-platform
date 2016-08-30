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
        kwargs['body'] = open(body_file).read()
        return kwargs

    def load_policies():
        load.run(force=True)


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

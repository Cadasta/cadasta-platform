import factory

from ..models import Organization, Project


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    name = factory.Sequence(lambda n: "Organization #%s" % n)
    slug = factory.Sequence(lambda n: "organization-%s" % n)
    description = factory.Sequence(
        lambda n: "Organization #%s description" % n)
    urls = ['http://example.com']
    contacts = []

    @factory.post_generation
    def add_users(self, create, users, **kwargs):
        if not create:
            return

        if users:
            for u in users:
                self.users.add(u)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: "Project #%s" % n)
    project_slug = factory.Sequence(lambda n: "project-%s" % n)
    organization = factory.SubFactory(OrganizationFactory)
    description = factory.Sequence(
                  lambda n: "Project #%s description" % n)
    urls = ['http://example.com']
    contacts = []

    @factory.post_generation
    def add_users(self, create, users, **kwargs):
        if not create:
            return

        if users:
            for u in users:
                self.users.add(u)

def clause(effect, action, object=None):
    if object is None:
        return {'effect': effect, 'action': action}
    else:
        return {'effect': effect, 'action': action, 'object': object}

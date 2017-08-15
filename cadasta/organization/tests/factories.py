import factory

from django.contrib.auth.models import Group
from core.tests.factories import ExtendedFactory
from ..models import Organization, OrganizationRole, Project, ProjectRole


class OrganizationFactory(ExtendedFactory):
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
                group = Group.objects.get(name='OrgMember')
                OrganizationRole.objects.create(organization=self,
                                                group=group, user=u)


class ProjectFactory(ExtendedFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: "Project #%s" % n)
    slug = factory.Sequence(lambda n: "project-%s" % n)
    organization = factory.SubFactory(OrganizationFactory)
    description = factory.Sequence(
        lambda n: "Project #%s description" % n)
    urls = ['http://example.com']
    contacts = []
    access = "public"

    @factory.post_generation
    def add_users(self, create, users, **kwargs):
        if not create:
            return

        if users:
            for u in users:
                if not OrganizationRole.objects.filter(
                        organization=self.organization, user=u).exists():
                    om = Group.objects.get(name='OrgMember')
                    OrganizationRole.objects.create(
                        organization=self.organization,
                        group=om, user=u)
                pu = Group.objects.get(name="ProjectMember")
                ProjectRole.objects.create(project=self, user=u,
                                           group=pu, role='PU')


def clause(effect, action, object=None):
    if object is None:
        return {'effect': effect, 'action': action}
    else:
        return {'effect': effect, 'action': action, 'object': object}

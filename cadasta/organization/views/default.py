import os
import json
from django.http import Http404, HttpResponse
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
import django.views.generic as base_generic
from django.core.urlresolvers import reverse
from django.utils.translation import gettext as _
from django.contrib import messages

import formtools.wizard.views as wizard

from tutelary.models import check_perms

import core.views.generic as generic
from core.views.mixins import SuperUserCheckMixin
from core.mixins import PermissionRequiredMixin, LoginPermissionRequiredMixin
from core.views.mixins import ArchiveMixin
from accounts.models import User
from questionnaires.models import Questionnaire
from questionnaires.exceptions import InvalidXLSForm
from spatial.serializers import SpatialUnitGeoJsonSerializer

from ..models import Organization, Project, OrganizationRole, ProjectRole
from . import mixins
from .. import forms
from .. import messages as error_messages


class OrganizationList(PermissionRequiredMixin, generic.ListView):
    model = Organization
    template_name = 'organization/organization_list.html'
    permission_required = 'org.list'
    permission_filter_queryset = ('org.view',)


class OrganizationAdd(LoginPermissionRequiredMixin, generic.CreateView):
    model = Organization
    form_class = forms.OrganizationForm
    template_name = 'organization/organization_add.html'
    permission_required = 'org.create'

    def get_perms_objects(self):
        return []

    def get_success_url(self):
        return reverse(
            'organization:dashboard',
            kwargs={'slug': self.object.slug}
        )

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['user'] = self.request.user
        return kwargs


class OrganizationDashboard(PermissionRequiredMixin,
                            mixins.OrganizationUICheckMixin,
                            generic.DetailView):
    model = Organization
    template_name = 'organization/organization_dashboard.html'
    permission_required = 'org.view'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data()
        if self.is_superuser:
            projects = self.object.all_projects()
        else:
            projects = self.object.public_projects()
            if hasattr(self.request.user, 'organizations'):
                orgs = self.request.user.organizations.all()
                for org in orgs:
                    if org.slug == self.kwargs['slug']:
                        projects = self.object.all_projects()
        context['projects'] = projects
        return super(generic.DetailView, self).render_to_response(context)


class OrganizationEdit(LoginPermissionRequiredMixin,
                       generic.UpdateView):
    model = Organization
    form_class = forms.OrganizationForm
    template_name = 'organization/organization_edit.html'
    permission_required = 'org.update'
    permission_denied_message = error_messages.ORG_EDIT

    def get_success_url(self):
        return reverse(
            'organization:dashboard',
            kwargs={'slug': self.object.slug}
        )


class OrgArchiveView(LoginPermissionRequiredMixin,
                     ArchiveMixin,
                     generic.DetailView):
    model = Organization

    def get_success_url(self):
        return reverse(
            'organization:dashboard',
            kwargs={'slug': self.object.slug}
        )


class OrganizationArchive(OrgArchiveView):
    permission_required = 'org.archive'
    permission_denied_message = error_messages.ORG_ARCHIVE
    do_archive = True


class OrganizationUnarchive(OrgArchiveView):
    permission_required = 'org.unarchive'
    permission_denied_message = error_messages.ORG_UNARCHIVE
    do_archive = False


class OrganizationMembers(LoginPermissionRequiredMixin,
                          mixins.OrganizationUICheckMixin,
                          generic.DetailView):
    model = Organization
    template_name = 'organization/organization_members.html'
    permission_required = 'org.users.list'
    permission_denied_message = error_messages.ORG_USERS_LIST


class OrganizationMembersAdd(mixins.OrganizationMixin,
                             LoginPermissionRequiredMixin,
                             generic.CreateView):
    model = OrganizationRole
    form_class = forms.AddOrganizationMemberForm
    template_name = 'organization/organization_members_add.html'
    permission_required = 'org.users.add'
    permission_denied_message = error_messages.ORG_USERS_ADD

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['organization'] = self.get_organization()
        return context

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)

        if self.request.method == 'POST':
            kwargs['organization'] = self.get_organization()

        return kwargs

    def get_success_url(self):
        return reverse(
            'organization:members_edit',
            kwargs={'slug': self.object.organization.slug,
                    'username': self.object.user.username}
        )


class OrganizationMembersEdit(mixins.OrganizationMixin,
                              LoginPermissionRequiredMixin,
                              mixins.OrganizationUICheckMixin,
                              base_generic.edit.FormMixin,
                              generic.DetailView):
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'organization/organization_members_edit.html'
    form_class = forms.EditOrganizationMemberForm
    permission_required = 'org.users.edit'
    permission_denied_message = error_messages.ORG_USERS_EDIT

    def get_success_url(self):
        return reverse(
            'organization:members',
            kwargs={'slug': self.get_organization().slug}
        )

    def get_queryset(self):
        return self.get_organization().users.all()

    def get_form(self):
        if self.request.method == 'POST':
            return self.form_class(self.request.POST,
                                   self.get_organization(),
                                   self.get_object())
        else:
            return self.form_class(None,
                                   self.get_organization(),
                                   self.get_object())

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['organization'] = self.get_organization()
        context['form'] = self.get_form()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class OrganizationMembersRemove(mixins.OrganizationMixin,
                                LoginPermissionRequiredMixin,
                                generic.DeleteView):
    permission_required = 'org.users.remove'
    permission_denied_message = error_messages.ORG_USERS_REMOVE

    def get_object(self):
        return OrganizationRole.objects.get(
            organization__slug=self.kwargs['slug'],
            user__username=self.kwargs['username'],
        )

    def get_success_url(self):
        return reverse(
            'organization:members',
            kwargs={'slug': self.get_organization().slug}
        )

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class UserList(LoginPermissionRequiredMixin, generic.ListView):
    model = User
    template_name = 'organization/user_list.html'
    permission_required = 'user.list'
    permission_denied_message = error_messages.USERS_LIST

    def get_context_data(self, **kwargs):
        context = super(UserList, self).get_context_data(**kwargs)
        for user in self.object_list:
            if user.organizations.count() == 0:
                user.org_names = '&mdash;'
            else:
                user.org_names = ', '.join(
                    sorted(map(lambda o: o.name, user.organizations.all()))
                )
        return context


class UserActivation(LoginPermissionRequiredMixin, base_generic.View):
    permission_required = 'user.update'
    permission_denied_message = error_messages.USERS_UPDATE
    new_state = None

    def get_perms_objects(self):
        return [get_object_or_404(User, username=self.kwargs['user'])]

    def post(self, request, user):
        userobj = get_object_or_404(User, username=user)
        userobj.is_active = self.new_state
        userobj.save()
        return redirect('user:list')


class ProjectList(PermissionRequiredMixin,
                  mixins.ProjectQuerySetMixin, generic.ListView):
    model = Project
    template_name = 'organization/project_list.html'
    permission_required = 'project.list'
    permission_filter_queryset = (lambda self, view, p: ('project.view',)
                                  if p.access == 'public'
                                  else ('project.view_private',))

    def add_allowed(self):
        retval = Organization.objects.count() > 0
        if retval:
            u = self.request.user
            if hasattr(u, 'organizations'):
                retval = any([
                    check_perms(u, ('project.create',), (o,))
                    for o in u.organizations.all()
                ])
            else:
                retval = False
        return self.is_superuser or retval

    def get_context_data(self, **kwargs):
        context = super(ProjectList, self).get_context_data(**kwargs)
        context['add_allowed'] = self.add_allowed()
        return context

    def get(self, request, *args, **kwargs):
        if (hasattr(self.request.user, 'assigned_policies') and
           self.is_superuser):
                projects = Project.objects.all()
        else:
            projects = []
            projects.extend(Project.objects.filter(access='public'))
            if hasattr(self.request.user, 'organizations'):
                user_orgs = self.request.user.organizations.all()
                for org in Organization.objects.all():
                    if org in user_orgs:
                        projects.extend(org.projects.filter(access='private'))
        self.object_list = sorted(
            projects, key=lambda p: p.organization.slug + ':' + p.slug)
        context = self.get_context_data()
        return super(generic.ListView, self).render_to_response(context)


class ProjectDashboard(PermissionRequiredMixin,
                       mixins.ProjectAdminCheckMixin,
                       generic.DetailView):
    def get_actions(view, request):
        if view.get_object().public():
            return 'project.view'
        else:
            return 'project.view_private'

    model = Project
    template_name = 'organization/project_dashboard.html'
    permission_required = {'GET': get_actions}
    permission_denied_message = error_messages.PROJ_VIEW

    def get_context_data(self, **kwargs):
        context = super(ProjectDashboard, self).get_context_data(**kwargs)
        num_locations = self.object.spatial_units.count()
        num_parties = self.object.parties.count()
        num_resources = self.object.resource_set.count()
        context['has_content'] = (
            num_locations > 0 or num_parties > 0 or num_resources > 0)
        context['num_locations'] = num_locations
        context['num_parties'] = num_parties
        context['num_resources'] = num_resources
        context['geojson'] = json.dumps(
            SpatialUnitGeoJsonSerializer(
                self.object.spatial_units.all(), many=True).data
        )

        return context

    def get_object(self, queryset=None):
        queryset = Project.objects.filter(
            organization__slug=self.kwargs.get('organization'),
            slug=self.kwargs.get('project')
        )
        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No projects found matching the query"))
        return obj


PROJECT_ADD_FORMS = [('extents', forms.ProjectAddExtents),
                     ('details', forms.ProjectAddDetails),
                     ('permissions', forms.ProjectAddPermissions)]

PROJECT_ADD_TEMPLATES = {
    'extents': 'organization/project_add_extents.html',
    'details': 'organization/project_add_details.html',
    'permissions': 'organization/project_add_permissions.html'
}


def add_wizard_permission_required(self, view, request):
    if request.method != 'POST':
        return ()
    session = request.session.get('wizard_project_add_wizard', None)
    if session is None or 'details' not in session['step_data']:
        return ()
    else:
        return 'project.create'


class ProjectAddWizard(SuperUserCheckMixin,
                       LoginPermissionRequiredMixin,
                       wizard.SessionWizardView):
    permission_required = add_wizard_permission_required
    form_list = PROJECT_ADD_FORMS

    def get_form_initial(self, step):
        initial = super().get_form_initial(step)

        if step == 'details' and self.kwargs.get('organization'):
            initial['organization'] = self.kwargs.get('organization')

        return initial

    def get_perms_objects(self):
        session = self.request.session.get('wizard_project_add_wizard', None)
        if session is None or 'details' not in session['step_data']:
            return []
        else:
            slug = session['step_data']['details']['details-organization'][0]
            return [Organization.objects.get(slug=slug)]

    def get_template_names(self):
        return [PROJECT_ADD_TEMPLATES[self.steps.current]]

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        orgs = Organization.objects.order_by('name')
        context['org_logos'] = {o.slug: o.logo for o in orgs}
        logo = orgs.first().logo if orgs.first() is not None else ''
        context['init_org_logo'] = logo
        context['init_org_hidden'] = 'org-logo-hidden' if logo is None else ''
        context['display_org'] = self.kwargs.get('organization')
        form = context['wizard']['form']
        if isinstance(form, forms.ProjectAddExtents):
            context['wizard_step_classes'] = {
                'extent': 'active enabled',
                'details': '',
                'permissions': ''
            }
        elif isinstance(form, forms.ProjectAddDetails):
            context['wizard_step_classes'] = {
                'extent': 'enabled complete',
                'details': 'active enabled',
                'permissions': ''
            }
        elif isinstance(form, forms.ProjectAddPermissions):
            context['wizard_step_classes'] = {
                'extent': 'enabled complete',
                'details': 'enabled complete',
                'permissions': 'active enabled'
            }
        return context

    def process_step(self, form):
        result = self.get_form_step_data(form)

        if 'details-organization' in result:
            self.organization = result['details-organization']

        return result

    def get_form_kwargs(self, step=None):
        if step == 'details':
            return {
                'user': self.request.user
            }
        elif step == 'permissions':
            return {
                'organization': self.get_cleaned_data_for_step(
                    'details').get('organization')
            }
        else:
            return {}

    def done(self, form_list, form_dict, **kwargs):
        form_data = [form.cleaned_data for form in form_list]
        extent = form_data[0]['extent']
        name = form_data[1]['name']
        description = form_data[1]['description']
        organization = form_data[1]['organization']
        url = form_data[1]['url']
        questionaire = form_data[1].get('questionaire')
        access = form_data[1].get('access')
        org = Organization.objects.get(slug=organization)

        user_roles = []
        for user in org.users.all():
            role = form_data[2].get(user.username, None)
            if role:
                user_roles.append((user, role))

        with transaction.atomic():
            project = Project.objects.create(
                name=name, organization=org,
                description=description, urls=[url], extent=extent,
                access=access
            )
            for username, role in user_roles:
                user = User.objects.get(username=username)
                ProjectRole.objects.create(
                    project=project, user=user, role=role
                )

            if questionaire:
                try:
                    Questionnaire.objects.create_from_form(
                        project=project,
                        xls_form=questionaire
                    )
                except InvalidXLSForm as e:
                    messages.warning(self.request, e)

        return redirect('organization:project-dashboard',
                        organization=organization,
                        project=project.slug)


class ProjectEdit(mixins.ProjectMixin,
                  LoginPermissionRequiredMixin):
    model = Project
    permission_required = 'project.update'

    def get_object(self):
        return self.get_project()

    def get_success_url(self):
        return reverse(
            'organization:project-dashboard',
            kwargs={
                'organization': self.object.organization.slug,
                'project': self.object.slug
            }
        )


class ProjectEditGeometry(ProjectEdit, generic.UpdateView):
    form_class = forms.ProjectAddExtents
    template_name = 'organization/project_edit_geometry.html'
    permission_denied_message = error_messages.PROJ_EDIT


class ProjectEditDetails(ProjectEdit, generic.UpdateView):
    form_class = forms.ProjectEditDetails
    template_name = 'organization/project_edit_details.html'
    permission_denied_message = error_messages.PROJ_EDIT

    def get_initial(self):
        initial = super().get_initial()

        try:
            questionnaire = Questionnaire.objects.get(
                id=self.object.current_questionnaire)
            initial['questionnaire'] = questionnaire.xls_form.url
        except Questionnaire.DoesNotExist:
            pass

        return initial

    def post(self, *args, **kwargs):
        try:
            return super().post(*args, **kwargs)
        except InvalidXLSForm as e:
            form = self.get_form()
            for err in e.errors:
                form.add_error('questionnaire', err)
            return self.form_invalid(form)


class ProjectEditPermissions(ProjectEdit, generic.UpdateView):
    form_class = forms.ProjectEditPermissions
    template_name = 'organization/project_edit_permissions.html'
    permission_denied_message = error_messages.PROJ_EDIT


class ProjectArchive(ProjectEdit, ArchiveMixin, generic.DetailView):
    permission_required = 'project.archive'
    permission_denied_message = error_messages.PROJ_ARCHIVE
    do_archive = True


class ProjectUnarchive(ProjectEdit, ArchiveMixin, generic.DetailView):
    permission_required = 'project.unarchive'
    permission_denied_message = error_messages.PROJ_UNARCHIVE
    do_archive = False


class ProjectDataDownload(mixins.ProjectMixin,
                          LoginPermissionRequiredMixin,
                          base_generic.edit.FormMixin,
                          generic.DetailView):
    template_name = 'organization/project_download.html'
    permission_required = 'project.download'
    permission_denied_message = error_messages.PROJ_DOWNLOAD
    form_class = forms.DownloadForm

    def get_object(self):
        return self.get_project()

    def get_form_kwargs(self, *args, **kwargs):
        kwargs = super().get_form_kwargs(*args, **kwargs)
        kwargs['project'] = self.object
        kwargs['user'] = self.request.user
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            path, mime_type = form.get_file()
            filename, ext = os.path.splitext(path)
            response = HttpResponse(open(path, 'rb'), content_type=mime_type)
            response['Content-Disposition'] = ('attachment; filename=' +
                                               self.object.slug + ext)
            return response

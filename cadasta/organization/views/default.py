import importlib
import os
from collections import OrderedDict

import core.views.generic as generic
import django.views.generic as base_generic
import formtools.wizard.views as wizard
from accounts.models import User
from core.mixins import (LoginPermissionRequiredMixin, PermissionRequiredMixin,
                         update_permissions)
from core.util import random_id
from core.views import mixins as core_mixins
from django.conf import settings
from django.core.files.storage import DefaultStorage, FileSystemStorage
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Sum, When, Case, IntegerField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from questionnaires.exceptions import InvalidQuestionnaire
from questionnaires.models import Questionnaire
from resources.models import ContentObject, Resource
from core.form_mixins import get_types
from party.choices import TENURE_RELATIONSHIP_TYPES
from spatial.choices import TYPE_CHOICES

from . import mixins
from .. import messages as error_messages
from .. import forms
from ..importers.exceptions import DataImportError
from ..models import Organization, OrganizationRole, Project, ProjectRole


class OrganizationList(PermissionRequiredMixin, generic.ListView):
    model = Organization
    template_name = 'organization/organization_list.html'
    permission_required = 'org.list'
    permission_filter_queryset = (lambda self, view, o: ('org.view',)
                                  if o.archived is False
                                  else ('org.view_archived',))

    # This queryset annotation is needed to avoid generating a query for each
    # organization in order to count the number of projects per org
    queryset = Organization.objects.annotate(
        num_projects=Sum(
            Case(
                When(projects__archived=False, then=1),
                default=0,
                output_field=IntegerField(),
            ),
        ),
    )


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
                            mixins.OrgRoleCheckMixin,
                            mixins.ProjectCreateCheckMixin,
                            core_mixins.CacheObjectMixin,
                            generic.DetailView):

    def get_actions(self, view, request):
        if self.get_object().archived:
            return 'org.view_archived'
        return 'org.view'

    model = Organization
    template_name = 'organization/organization_dashboard.html'
    permission_required = get_actions
    permission_denied_message = error_messages.ORG_VIEW

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
                        if self.is_administrator:
                            projects = self.object.all_projects()
                        else:
                            projects = self.object.all_projects().filter(
                                archived=False)

        context['projects'] = projects
        return super(generic.DetailView, self).render_to_response(context)


class OrganizationEdit(LoginPermissionRequiredMixin,
                       core_mixins.CacheObjectMixin,
                       generic.UpdateView):
    model = Organization
    form_class = forms.OrganizationForm
    template_name = 'organization/organization_edit.html'
    permission_required = update_permissions('org.update', True)
    permission_denied_message = error_messages.ORG_EDIT

    def get_success_url(self):
        return reverse('organization:dashboard', kwargs=self.kwargs)


class OrgArchiveView(LoginPermissionRequiredMixin,
                     core_mixins.ArchiveMixin,
                     generic.DetailView):
    model = Organization

    def get_success_url(self):
        return reverse('organization:dashboard', kwargs=self.kwargs)

    def archive(self):
        assert hasattr(self, 'do_archive'), "Please set do_archive attribute"
        self.object = self.get_object()
        self.object.archived = self.do_archive
        self.object.save()
        for project in self.object.projects.all():
            project.archived = self.do_archive
            project.save()
        return redirect(self.get_success_url())


class OrganizationArchive(OrgArchiveView):
    permission_required = 'org.archive'
    permission_denied_message = error_messages.ORG_ARCHIVE
    do_archive = True


class OrganizationUnarchive(OrgArchiveView):
    permission_required = 'org.unarchive'
    permission_denied_message = error_messages.ORG_UNARCHIVE
    do_archive = False


class OrganizationMembers(LoginPermissionRequiredMixin,
                          mixins.OrgRoleCheckMixin,
                          mixins.ProjectCreateCheckMixin,
                          core_mixins.CacheObjectMixin,
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
    permission_required = update_permissions('org.users.add')
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
                              mixins.OrgRoleCheckMixin,
                              mixins.ProjectCreateCheckMixin,
                              core_mixins.CacheObjectMixin,
                              base_generic.edit.FormMixin,
                              generic.DetailView):
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'
    template_name = 'organization/organization_members_edit.html'
    project_form_class = forms.EditOrganizationMemberProjectPermissionForm
    org_role_form_class = forms.EditOrganizationMemberForm
    permission_required = update_permissions('org.users.edit')
    permission_denied_message = error_messages.ORG_USERS_EDIT

    def get_success_url(self):
        if self.request.POST and self.request.POST.get('org_role'):
            return reverse(
                 'organization:members_edit',
                 kwargs=self.kwargs,
            )

        return reverse(
            'organization:members',
            kwargs={'slug': self.kwargs['slug']},
        )

    def get_context_object_name(self, obj):
        # Dummy context so that the currently viewed user does not
        # override the logged-in user
        return 'org_member'

    def get_form(self):
        if not hasattr(self, 'org_form'):
            data = self.request.POST if self.request.POST else None
            self.org_form = self.org_role_form_class(
                self.get_organization(),
                self.get_object(),
                self.request.user,
                data=data)

        return self.org_form

    def get_prj_role_form(self):
        if not hasattr(self, 'prj_form'):
            data = self.request.POST if self.request.POST else None
            self.prj_form = self.project_form_class(
                self.get_organization(),
                self.get_object(),
                self.request.user,
                data=data)

        return self.prj_form

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['organization'] = self.get_organization()
        context['project_role_form'] = self.get_prj_role_form()
        context['org_role_form'] = self.get_form()

        context['org_admin'] = OrganizationRole.objects.filter(
            user=context['org_member'],
            organization=context['organization'],
            admin=True).exists()
        context['current_user'] = (
            context['org_member'] == self.request.user and
            not self.is_superuser)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if 'org_role' in request.POST:
            form = self.get_form()
        else:
            form = self.get_prj_role_form()

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
    permission_required = update_permissions('org.users.remove')
    permission_denied_message = error_messages.ORG_USERS_REMOVE

    def get_object(self):
        return OrganizationRole.objects.get(
            organization__slug=self.kwargs['slug'],
            user__username=self.kwargs['username'],
        )

    def get_success_url(self):
        return reverse(
            'organization:members',
            kwargs={'slug': self.kwargs['slug']},
        )

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class UserList(LoginPermissionRequiredMixin, generic.ListView):
    model = User
    template_name = 'organization/user_list.html'
    permission_required = 'user.list'
    permission_denied_message = error_messages.USERS_LIST

    def get_queryset(self):
        # Since we are querying on the organizations of each user, we should
        # prefetch the organizations when querying for all users instead of
        # doing a separate organizations query for every user
        return User.objects.prefetch_related('organizations')

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
                  mixins.ProjectQuerySetMixin,
                  mixins.ProjectCreateCheckMixin,
                  generic.ListView):

    def permission_filter(self, view, p):
        if p.archived is True:
            return ('project.view_archived',)
        elif p.access == 'private':
            return ('project.view_private',)
        else:
            return ('project.view',)

    model = Project
    template_name = 'organization/project_list.html'
    permission_required = 'project.list'
    permission_filter_queryset = permission_filter
    project_create_check_multiple = True

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if self.is_superuser:
            projects = Project.objects.select_related('organization')
        else:
            projects = []
            projects.extend(Project.objects.filter(
                access='public', archived=False).select_related(
                    'organization'))
            if hasattr(user, 'organizations'):
                for org in user.organizations.all():
                    projects.extend(org.projects.filter(
                        access='private', archived=False).select_related(
                            'organization'))
                    if OrganizationRole.objects.get(organization=org,
                                                    user=user).admin is True:
                        projects.extend(org.projects.filter(
                            archived=True).select_related('organization'))
        self.object_list = sorted(
            projects, key=lambda p: p.organization.slug + ':' + p.slug)
        context = self.get_context_data()
        return super().render_to_response(context)


class ProjectDashboard(PermissionRequiredMixin,
                       mixins.ProjectAdminCheckMixin,
                       mixins.ProjectMixin,
                       generic.DetailView):

    def get_actions(self, view):
        if self.prj.archived:
            return 'project.view_archived'
        if self.prj.public():
            return 'project.view'
        else:
            return 'project.view_private'

    model = Project
    template_name = 'organization/project_dashboard.html'
    permission_required = {'GET': get_actions}
    permission_denied_message = error_messages.PROJ_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        members = OrderedDict()

        # add org_admin users
        for member in self.object.organization.users.all():
            roles = member.organizationrole_set.filter(
                organization=self.object.organization, admin=True)
            if roles:
                members[member.username] = 'Administrator'

        # add project members
        for member in self.object.users.all():
            role = member.projectrole_set.filter(project=self.object)[0]
            role_name = role.get_role_display()
            members[member.username] = role_name
        num_locations = self.object.spatial_units.count()
        num_parties = self.object.parties.count()
        num_resources = self.object.resource_set.filter(archived=False).count()
        context['has_content'] = (
            num_locations > 0 or num_parties > 0 or num_resources > 0)
        context['num_locations'] = num_locations
        context['num_parties'] = num_parties
        context['num_resources'] = num_resources
        context['members'] = members
        try:
            context['questionnaire'] = Questionnaire.objects.get(
                id=self.object.current_questionnaire)
        except Questionnaire.DoesNotExist:
            pass

        return context

    def get_object(self, queryset=None):
        return self.get_project()


PROJECT_ADD_FORMS = [('extents', forms.ProjectAddExtents),
                     ('details', forms.ProjectAddDetails),
                     ('permissions', forms.ProjectAddPermissions)]

PROJECT_ADD_TEMPLATES = {
    'extents': 'organization/project_add_extents.html',
    'details': 'organization/project_add_details.html',
    'permissions': 'organization/project_add_permissions.html'
}


def add_wizard_permission_required(self, view, request):
    if 'organization' in self.kwargs:
        if Organization.objects.get(
                slug=self.kwargs.get('organization')).archived:
            return False
    if request.method != 'POST':
        return ()
    session = request.session.get('wizard_project_add_wizard', None)
    if session is None or 'details' not in session['step_data']:
        return ()
    else:
        return 'project.create'


class ProjectAddWizard(core_mixins.SuperUserCheckMixin,
                       LoginPermissionRequiredMixin,
                       wizard.SessionWizardView):
    permission_required = add_wizard_permission_required
    form_list = PROJECT_ADD_FORMS

    class RevalidationError(Exception):

        def __init__(self, step, form, **kwargs):
            self.step = step
            self.form = form
            self.kwargs = kwargs

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

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form, **kwargs)
        if self.steps.current == 'extents':
            context['wizard_step_classes'] = {
                'extent': 'active enabled',
                'details': '',
                'permissions': ''
            }
        elif self.steps.current == 'details':
            context['wizard_step_classes'] = {
                'extent': 'enabled complete',
                'details': 'active enabled',
                'permissions': ''
            }
            context['org_logos'] = {
                o.slug: o.logo for o in form.orgs if o.logo
            }
            context['display_org'] = self.kwargs.get('organization')
        elif self.steps.current == 'permissions':
            context['wizard_step_classes'] = {
                'extent': 'enabled complete',
                'details': 'enabled complete',
                'permissions': 'active enabled'
            }
        return context

    def process_step(self, form):
        if self.steps.current == 'details':
            self.storage.extra_data['org_is_chosen'] = True

        result = self.get_form_step_data(form)
        if 'details-organization' in result:
            self.storage.extra_data['organization'] = (
                result['details-organization'])
        return result

    def render_goto_step(self, goto_step, **kwargs):
        form = self.get_form(data=self.request.POST, files=self.request.FILES)
        if form.is_valid():
            self.storage.set_step_data(self.steps.current,
                                       self.process_step(form))
            self.storage.set_step_files(self.steps.current,
                                        self.process_step_files(form))
        return super().render_goto_step(goto_step, **kwargs)

    def get_form_kwargs(self, step=None):
        if step == 'details':
            return {
                'user': self.request.user,
                'org_is_chosen': self.storage.extra_data.get('org_is_chosen'),
            }
        elif step == 'permissions':
            return {
                'organization': self.storage.extra_data['organization'],
            }
        else:
            return {}

    def done(self, form_list, form_dict, **kwargs):
        form_data = [form.cleaned_data for form in form_list]
        extent = form_data[0]['extent']
        organization = form_data[1]['organization']
        name = form_data[1]['name']
        description = form_data[1]['description']
        access = form_data[1].get('access')
        url = form_data[1]['url']
        questionnaire = form_data[1].get('questionnaire')
        original_file = form_data[1].get('original_file')
        contacts = form_data[1].get('contacts')

        org = Organization.objects.get(slug=organization)

        user_roles = []
        for user in org.users.all():
            role = form_data[2].get(user.username, None)
            if role and role != 'Pb':
                user_roles.append((user, role))
        try:
            with transaction.atomic():
                project = Project.objects.create(
                    name=name, organization=org,
                    description=description, urls=[url], extent=extent,
                    access=access, contacts=contacts
                )
                for username, role in user_roles:
                    user = User.objects.get(username=username)
                    ProjectRole.objects.create(
                        project=project, user=user, role=role
                    )
                if questionnaire:
                    Questionnaire.objects.create_from_form(
                        project=project,
                        original_file=original_file,
                        xls_form=questionnaire
                    )
        except InvalidQuestionnaire as e:
            details_form = form_dict['details']
            details_form.add_error('questionnaire', e)
            raise self.RevalidationError('details', details_form, **kwargs)

        return redirect('organization:project-dashboard',
                        organization=organization,
                        project=project.slug)

    def render_done(self, form, **kwargs):
        final_forms = OrderedDict()
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            if not form_obj.is_valid():  # pragma:  no cover
                return self.render_revalidation_failure(
                    form_key, form_obj, **kwargs
                )
            final_forms[form_key] = form_obj

        # catch bad xform here
        try:
            done_response = self.done(
                final_forms.values(), form_dict=final_forms, **kwargs
            )
        except self.RevalidationError as e:
            return self.render_revalidation_failure(
                e.step, e.form, **e.kwargs
            )
        self.storage.reset()
        return done_response


class ProjectEdit(mixins.ProjectMixin,
                  mixins.ProjectAdminCheckMixin,
                  LoginPermissionRequiredMixin):
    model = Project
    permission_required = update_permissions('project.update', True)

    def get_object(self):
        return self.get_project()

    def get_success_url(self):
        return reverse('organization:project-dashboard', kwargs=self.kwargs)


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
            initial['original_file'] = questionnaire.original_file
        except Questionnaire.DoesNotExist:
            pass

        return initial

    def post(self, *args, **kwargs):
        try:
            return super().post(*args, **kwargs)
        except InvalidQuestionnaire as e:
            form = self.get_form()
            for err in e.errors:
                form.add_error('questionnaire', err)
            return self.form_invalid(form)

    def form_invalid(self, form):
        project = self.get_project()
        project.refresh_from_db(fields=('current_questionnaire', ))
        context = self.get_context_data(object=project, form=form)
        return self.render_to_response(context)


class ProjectEditPermissions(ProjectEdit, generic.UpdateView):
    form_class = forms.ProjectEditPermissions
    template_name = 'organization/project_edit_permissions.html'
    permission_denied_message = error_messages.PROJ_EDIT


class ProjectArchive(ProjectEdit,
                     core_mixins.ArchiveMixin,
                     generic.DetailView):
    permission_required = 'project.archive'
    permission_denied_message = error_messages.PROJ_ARCHIVE
    do_archive = True


class ProjectUnarchive(ProjectEdit,
                       core_mixins.ArchiveMixin,
                       generic.DetailView):

    def patch_actions(self, request, view=None):
        if self.get_organization().archived:
            return False
        return 'project.unarchive'
    permission_required = patch_actions
    permission_denied_message = error_messages.PROJ_UNARCHIVE
    do_archive = False


class ProjectDataDownload(mixins.ProjectMixin,
                          LoginPermissionRequiredMixin,
                          mixins.ProjectAdminCheckMixin,
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


DATA_IMPORT_FORMS = [('select_file', forms.SelectImportForm),
                     ('map_attributes', forms.MapAttributesForm),
                     ('select_defaults', forms.SelectDefaultsForm)]

DATA_IMPORT_TEMPLATES = {
    'select_file': 'organization/project_select_import.html',
    'map_attributes': 'organization/project_attrs_import.html',
    'select_defaults': 'organization/project_defaults_import.html'
}


class ProjectDataImportWizard(mixins.ProjectMixin,
                              LoginPermissionRequiredMixin,
                              mixins.ProjectAdminCheckMixin,
                              wizard.SessionWizardView):
    permission_required = 'project.import'
    permission_denied_message = error_messages.PROJ_IMPORT
    form_list = DATA_IMPORT_FORMS
    file_storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, 'temp'))

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['object'] = self.get_object()
        if self.steps.current == 'select_file':
            context['wizard_step_classes'] = {
                'select_file': 'active enabled',
                'map_attributes': '',
                'select_defaults': ''
            }
        elif self.steps.current == 'map_attributes':
            context['wizard_step_classes'] = {
                'select_file': 'enabled complete',
                'map_attributes': 'active enabled',
                'select_defaults': ''
            }
        elif self.steps.current == 'select_defaults':
            context['wizard_step_classes'] = {
                'select_file': 'enabled complete',
                'map_attributes': 'enabled complete',
                'select_defaults': 'active enabled'
            }
        return context

    def get_object(self):
        return self.get_project()

    def get_form_kwargs(self, step=None):
        return {
            'user': self.request.user,
            'project': self.get_project()
        }

    def get_perms_objects(self):
        return [self.get_project()]

    def get_template_names(self):
        return [DATA_IMPORT_TEMPLATES[self.steps.current]]

    def render_goto_step(self, goto_step, **kwargs):
        self.storage.current_step = goto_step
        form = self.get_form(
            data=self.storage.get_step_data(self.steps.current),
            files=self.storage.get_step_files(self.steps.current))
        if goto_step == 'map_attributes':
            file = self.storage.get_step_files(
                'select_file')['select_file-file']
            type = self.storage.get_step_data('select_file')[
                'select_file-type']
            entity_types = self.storage.get_step_data('select_file').getlist(
                'select_file-entity_types'
            )
            path = self.file_storage.path(file.name)
            importer = self._get_importer(type, path)
            (attr_map,
                extra_attrs, extra_headers) = importer.get_attribute_map(
                    type, entity_types.copy(), flatten=True)

            return self.render(
                form, attr_map=attr_map,
                extra_attrs=extra_attrs, extra_headers=extra_headers, **kwargs
            )
        if goto_step == 'select_file':
            # delete file if user navigates back to first page
            form_key = 'select_file'
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            file = form_obj.files['select_file-file']
            self.file_storage.delete(file.name)
            return self.render(form_obj, **kwargs)
        return self.render(form)

    def render_next_step(self, form, **kwargs):
        next_step = self.steps.next
        new_form = self.get_form(
            next_step,
            data=self.storage.get_step_data(next_step),
            files=self.storage.get_step_files(next_step),
        )
        self.storage.current_step = next_step
        if next_step == 'map_attributes':
            file = self.request.FILES.get('select_file-file')
            type = self.storage.get_step_data(
                'select_file').get('select_file-type')
            entity_types = self.storage.get_step_data('select_file').getlist(
                'select_file-entity_types'
            )
            path = self.file_storage.path(file.name)
            importer = self._get_importer(type, path)
            (attr_map,
                extra_attrs, extra_headers) = importer.get_attribute_map(
                    type, entity_types.copy(), flatten=True
            )
            return self.render(
                form, attr_map=attr_map,
                extra_attrs=extra_attrs, extra_headers=extra_headers, **kwargs
            )
        if next_step == 'select_defaults':
            heads = self.request.POST.get('extra_headers', None)
            available_headers = heads.split(',')
            entity_types = self.storage.get_step_data('select_file').getlist(
                'select_file-entity_types'
            )
            unique_headers = []
            for header in available_headers:
                if header not in unique_headers:
                    unique_headers.append(header)
            return self.render(
                new_form, available_headers=unique_headers,
                entity_types=entity_types, **kwargs
            )

    def done(self, form_list, **kwargs):
        form_data = [form.cleaned_data for form in form_list]
        name = form_data[0]['name']
        description = form_data[0]['description']
        mime_type = form_data[0]['mime_type']
        is_resource = form_data[0]['is_resource']
        original_file = form_data[0]['original_file']
        file = form_data[0]['file']
        type = self.storage.get_step_data(
            'select_file').get('select_file-type')
        entity_types = self.storage.get_step_data('select_file').getlist(
            'select_file-entity_types'
        )
        path = self.file_storage.path(file.name)
        map_attrs_data = self.storage.get_step_data('map_attributes')
        project = self.get_project()
        org = project.organization
        allowed_tenure_types = get_types(
            'tenure_type',
            TENURE_RELATIONSHIP_TYPES,
            questionnaire_id=project.current_questionnaire)
        allowed_location_types = get_types(
            'location_type',
            TYPE_CHOICES,
            questionnaire_id=project.current_questionnaire)

        config_dict = {
            'project': project,
            'file': path,
            'type': type,
            'entity_types': entity_types.copy(),
            'party_name_field': form_data[2]['party_name_field'],
            'party_type_field': form_data[2]['party_type_field'],
            'location_type_field': form_data[2]['location_type_field'],
            'geometry_field': form_data[2]['geometry_field'],
            'attributes': map_attrs_data.getlist('attributes', None),
            'allowed_tenure_types': allowed_tenure_types,
            'allowed_location_types': allowed_location_types
        }

        importer = self._get_importer(type, path)
        importer.import_data(config_dict)

        if is_resource:
            default_storage = DefaultStorage()
            file.seek(0)
            ext = file.name[file.name.rfind('.'):]
            resource = Resource(
                name=name, description=description,
                original_file=original_file, mime_type=mime_type,
                contributor=self.request.user, project=self.get_project())
            upload_to = getattr(resource.file.field, 'upload_to')
            url = ''
            while not url:
                temp_url = upload_to + '/' + random_id() + ext
                if not Resource.objects.filter(
                        file__contains=temp_url).exists():
                    url = default_storage.save(temp_url, file.read())
            resource.file.url = url
            resource.save()
            ContentObject.objects.create(resource=resource,
                                         content_object=resource.project)
        return redirect('organization:project-dashboard',
                        organization=org.slug,
                        project=project.slug)

    def render_done(self, form, **kwargs):
        final_forms = OrderedDict()
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            if not form_obj.is_valid():  # pragma:  no cover
                return self.render_revalidation_failure(
                    form_key, form_obj, **kwargs
                )
            final_forms[form_key] = form_obj

        # catch bad import here
        try:
            done_response = self.done(
                final_forms.values(), form_dict=final_forms, **kwargs
            )
        except DataImportError as e:
            form_key = 'select_file'
            form_obj = self.get_form(
                step=form_key,
                data=self.storage.get_step_data(form_key),
                files=self.storage.get_step_files(form_key)
            )
            form_obj.add_error('file', str(e))
            file = form_obj.files['select_file-file']
            self.file_storage.delete(file.name)
            return self.render_revalidation_failure(
                'select_file', form_obj, **kwargs
            )
        self.storage.reset()
        return done_response

    def _get_importer(self, type, path):
        fqn = settings.IMPORTERS.get(type)
        parts = fqn.rpartition('.')
        module = importlib.import_module(parts[0])
        clazz = parts[-1]
        importer = getattr(module, clazz)
        return importer(project=self.get_project(), path=path)

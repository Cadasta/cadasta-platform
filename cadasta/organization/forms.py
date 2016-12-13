import mimetypes
import time
from zipfile import ZipFile

from accounts.models import User
from buckets.widgets import S3FileUploadWidget
from core.form_mixins import SuperUserCheck
from core.util import slugify
from django import forms
from django.conf import settings
from django.contrib.gis import forms as gisforms
from django.contrib.postgres import forms as pg_forms
from django.db import transaction
from django.forms import ValidationError
from django.forms.utils import ErrorDict
from django.utils.translation import ugettext as _
from leaflet.forms.widgets import LeafletWidget
from questionnaires.models import Questionnaire
from tutelary.models import check_perms

from .choices import ADMIN_CHOICES, ROLE_CHOICES
from .download.resources import ResourceExporter
from .download.shape import ShapeExporter
from .download.xls import XLSExporter
from organization import fields as org_fields
from .models import Organization, OrganizationRole, Project, ProjectRole

FORM_CHOICES = (('Pb', _('Public User')),) + ROLE_CHOICES
QUESTIONNAIRE_TYPES = [
    'application/msexcel',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]


def create_update_or_delete_project_role(project, user, role):
    if role != 'Pb':
        ProjectRole.objects.update_or_create(
            user=user,
            project_id=project,
            defaults={'role': role})
    else:
        ProjectRole.objects.filter(user=user,
                                   project_id=project).delete()


class ContactsForm(forms.Form):
    name = forms.CharField()
    email = forms.EmailField(required=False)
    tel = forms.CharField(required=False)
    remove = forms.BooleanField(required=False, widget=forms.HiddenInput())

    def as_table(self):
        html = self._html_output(
            normal_row='<td>%(field)s%(help_text)s</td>',
            error_row=('<tr class="contacts-error {error_types}">'
                       '<td colspan="4">%s</td></tr>\n<tr>'),
            row_ender='</td>',
            help_text_html='<br /><span class="helptext">%s</span>',
            errors_on_separate_row=False)
        closeBtn = ('<td><a data-prefix="' + self.prefix + '" '
                    'class="close remove-contact" href="#">'
                    '<span aria-hidden="true">&times;</span></a></td>')
        html = ('' if self.errors else '<tr>') + html + closeBtn + '</tr>\n'

        error_types = ''
        if 'name' in self.errors:
            error_types += ' error-name'
        if 'email' in self.errors:
            error_types += ' error-email'
        if hasattr(self, 'contact_details_is_missing'):
            error_types += ' error-email error-phone'

        return html.format(error_types=error_types)

    def full_clean(self):
        if self.data.get(self.prefix + '-remove') != 'on':
            super().full_clean()
        else:
            self._errors = ErrorDict()
            self.cleaned_data = {'remove': True}

    def clean(self):
        cleaned_data = super().clean()
        error_msgs = []
        if 'name' in self.errors:
            error_msgs.append(_("Please provide a name."))
        if 'email' in self.errors:
            error_msgs.append(_("The provided email address is invalid."))
        if (
            not self.errors and
            not cleaned_data['email'] and
            not cleaned_data['tel']
        ):
            self.contact_details_is_missing = True
            error_msgs.append(_(
                "Please provide either an email address or a phone number."))
        if error_msgs:
            raise forms.ValidationError(" ".join(error_msgs))

        return cleaned_data

    def clean_string(self, value):
        if not value:
            return None
        return value

    def clean_email(self):
        return self.clean_string(self.cleaned_data['email'])

    def clean_tel(self):
        return self.clean_string(self.cleaned_data['tel'])


class OrganizationForm(forms.ModelForm):
    urls = pg_forms.SimpleArrayField(
        forms.URLField(required=False),
        required=False,
        error_messages={'item_invalid': ""},
    )
    contacts = org_fields.ContactsField(form=ContactsForm, required=False)
    access = org_fields.PublicPrivateField()

    class Meta:
        model = Organization
        fields = ['name', 'description', 'urls', 'contacts', 'access']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']
        invalid_names = settings.CADASTA_INVALID_ENTITY_NAMES
        if slugify(name, allow_unicode=True) in invalid_names:
            raise forms.ValidationError(
                _("Organization name cannot be “Add” or “New”."))
        return name

    def save(self, *args, **kwargs):
        instance = super().save(commit=False)
        is_create = not instance.id

        instance.save()

        if is_create:
            OrganizationRole.objects.create(
                organization=instance,
                user=self.user,
                admin=True
            )

        return instance


class AddOrganizationMemberForm(forms.Form):
    identifier = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.instance = kwargs.pop('instance', None)
        super(AddOrganizationMemberForm, self).__init__(*args, **kwargs)

    def clean_identifier(self):
        identifier = self.data.get('identifier')
        try:
            self.user = User.objects.get_from_username_or_email(
                identifier=identifier)
        except (User.DoesNotExist, User.MultipleObjectsReturned) as e:
            raise forms.ValidationError(e)
        user_exists = OrganizationRole.objects.filter(
            user=self.user, organization=self.organization).exists()
        if user_exists:
            raise forms.ValidationError(
                _("User is already a member of the organization."),
                code='member_already')

    def save(self):
        if self.errors:
            raise ValueError(
                _("The role could not be assigned because the data didn't "
                  "validate.")
            )

        self.instance = OrganizationRole.objects.create(
            organization=self.organization, user=self.user)
        return self.instance


class EditOrganizationMemberForm(SuperUserCheck, forms.Form):
    org_role = forms.ChoiceField(choices=ADMIN_CHOICES)

    def __init__(self, org, user, current_user, data=None, *args, **kwargs):
        super(EditOrganizationMemberForm, self).__init__(data, *args, **kwargs)
        self.data = data
        self.organization = org
        self.user = user
        self.current_user = current_user
        self.org_role_instance = OrganizationRole.objects.get(
            user=user,
            organization=self.organization)

        self.initial['org_role'] = 'A' if self.org_role_instance.admin else 'M'

    def clean_org_role(self):
        org_role = self.cleaned_data['org_role']
        if (self.org_role_instance.admin and
           self.current_user == self.user and
           not self.is_superuser(self.user)):
            if self.data.get('org_role') != 'A':
                raise forms.ValidationError(
                    _("Organization administrators cannot change their own" +
                        " role in the organization."))
        return org_role

    def save(self):
        self.org_role_instance.admin = self.data.get('org_role') == 'A'
        self.org_role_instance.save()


class EditOrganizationMemberProjectPermissionForm(forms.Form):
    def __init__(self, org, user, current_user, data=None, *args, **kwargs):
        super(EditOrganizationMemberProjectPermissionForm, self).__init__(
            data, *args, **kwargs)
        self.data = data
        self.organization = org
        self.user = user
        self.current_user = current_user
        self.org_role_instance = OrganizationRole.objects.get(
            user=user, organization=self.organization)

        project_roles = ProjectRole.objects.filter(
            user=user, project__organization=org).values('project__id', 'role')
        project_roles = {r['project__id']: r['role'] for r in project_roles}
        active_projects = self.organization.projects.filter(archived=False)

        for p in active_projects.values_list('id', 'name'):
            role = project_roles.get(p[0], 'Pb')
            self.fields[p[0]] = org_fields.ProjectRoleEditField(
                choices=FORM_CHOICES,
                label=p[1],
                required=(not self.org_role_instance.admin),
                initial=role,
                admin=self.org_role_instance.admin,
            )

    def save(self):
        for f in [field for field in self.fields]:
            role = self.data.get(f)
            create_update_or_delete_project_role(f, self.user, role)


class ProjectAddExtents(forms.ModelForm):
    extent = gisforms.PolygonField(widget=LeafletWidget(), required=False)

    class Meta:
        model = Project
        fields = ['extent']


class ProjectAddDetails(SuperUserCheck, forms.Form):

    class Media:
        js = ('js/file-upload.js',)

    organization = forms.ChoiceField()
    name = forms.CharField(max_length=100)
    description = forms.CharField(required=False, widget=forms.Textarea)
    access = org_fields.PublicPrivateField(initial='public')
    url = forms.URLField(required=False)
    questionnaire = forms.CharField(
        required=False,
        widget=S3FileUploadWidget(upload_to='xls-forms',
                                  accepted_types=QUESTIONNAIRE_TYPES))
    original_file = forms.CharField(required=False,
                                    max_length=200,
                                    widget=forms.HiddenInput)
    contacts = org_fields.ContactsField(form=ContactsForm, required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        org_is_chosen = kwargs.pop('org_is_chosen', None)
        super().__init__(*args, **kwargs)

        if self.is_superuser(self.user):
            self.orgs = Organization.objects.filter(
                archived=False).order_by('name')
        else:
            qs = self.user.organizations.filter(
                archived=False).order_by('name')
            self.orgs = [
                o for o in qs
                if check_perms(self.user, ('project.create',), (o,))
            ]
        choices = [(o.slug, o.name) for o in self.orgs]
        if not org_is_chosen and len(choices) > 1:
            choices = [('', _("Please select an organization"))] + choices
        self.fields['organization'].choices = choices

    def clean_name(self):
        name = self.cleaned_data['name']

        # Check that name is not restricted
        invalid_names = settings.CADASTA_INVALID_ENTITY_NAMES
        if slugify(name, allow_unicode=True) in invalid_names:
            raise forms.ValidationError(
                _("Project name cannot be “Add” or “New”."))

        # Check that name is unique org-wide
        # (Explicit validation because we are using a wizard and the
        # unique_together validation cannot occur in the proper page)
        if self.cleaned_data.get('organization'):
            not_unique = Project.objects.filter(
                organization__slug=self.cleaned_data['organization'],
                name=name,
            ).exists()
            if not_unique:
                raise forms.ValidationError(
                    _("Project with this name already exists "
                      "in this organization."))

        return name


class ProjectEditDetails(forms.ModelForm):
    urls = pg_forms.SimpleArrayField(
        forms.URLField(required=False),
        required=False,
        error_messages={'item_invalid': ""},
    )
    questionnaire = forms.CharField(
        required=False,
        widget=S3FileUploadWidget(upload_to='xls-forms',
                                  accepted_types=QUESTIONNAIRE_TYPES))
    original_file = forms.CharField(required=False,
                                    max_length=200,
                                    widget=forms.HiddenInput)
    access = org_fields.PublicPrivateField()
    contacts = org_fields.ContactsField(form=ContactsForm, required=False)

    class Media:
        js = ('js/file-upload.js',)

    class Meta:
        model = Project
        fields = ['name', 'description', 'access', 'urls', 'questionnaire',
                  'contacts']

    def clean_questionnaire(self):
        new_form = self.data.get('questionnaire')
        current_form = self.initial.get('questionnaire')

        if (new_form is not None and new_form != current_form and
                self.instance.has_records):
            raise ValidationError(
                _("Data has already been contributed to this project. To "
                  "ensure data integrity, uploading a new questionnaire is "
                  "disabled for this project."))

    def save(self, *args, **kwargs):
        new_form = self.data.get('questionnaire')
        original_file = self.data.get('original_file')
        current_form = self.initial.get('questionnaire')

        if new_form:
            if current_form != new_form:
                Questionnaire.objects.create_from_form(
                    xls_form=new_form,
                    original_file=original_file,
                    project=self.instance
                )
        elif new_form is not None and not self.instance.has_records:
            self.instance.current_questionnaire = ''

        return super().save(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data['name']

        # Check that name is not restricted
        invalid_names = settings.CADASTA_INVALID_ENTITY_NAMES
        if slugify(name, allow_unicode=True) in invalid_names:
            raise forms.ValidationError(
                _("Project name cannot be “Add” or “New”."))

        # Check that name is unique org-wide
        # (Explicit validation because we are using a wizard and the
        # unique_together validation cannot occur in the proper page)
        not_unique = Project.objects.filter(
            organization__slug=self.instance.organization.slug,
            name=name,
        ).exclude(id=self.instance.id).exists()
        if not_unique:
            raise forms.ValidationError(
                _("Project with this name already exists "
                  "in this organization."))

        return name


class PermissionsForm(SuperUserCheck):

    def check_admin(self, user):
        if not hasattr(self, 'admins'):
            self.admins = [
                role.user for role in OrganizationRole.objects.filter(
                    organization=self.organization,
                    admin=True
                ).select_related('user')
            ]

        return self.is_superuser(user) or user in self.admins

    def set_fields(self):
        for user in self.organization.users.all():
            if self.check_admin(user):
                role = 'A'
            else:
                if hasattr(self, 'project_roles'):
                    role = self.project_roles.get(user.id, 'Pb')
                else:
                    role = 'Pb'

            self.fields[user.username] = org_fields.ProjectRoleField(
                choices=FORM_CHOICES,
                label=user.full_name,
                required=(role != 'A'),
                initial=role,
                user=user
            )


class ProjectAddPermissions(PermissionsForm, forms.Form):

    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is not None:
            self.organization = Organization.objects.get(slug=organization)
            self.set_fields()


class ProjectEditPermissions(PermissionsForm, forms.Form):

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('instance')
        super().__init__(*args, **kwargs)
        self.organization = self.project.organization

        project_roles = ProjectRole.objects.filter(
            project=self.project).values('user__id', 'role')
        self.project_roles = {r['user__id']: r['role'] for r in project_roles}
        self.set_fields()

    def save(self):
        with transaction.atomic():
            for k, f in [
                (k, f) for k, f in self.fields.items() if f.initial != 'A'
            ]:
                role = self.data.get(k)
                create_update_or_delete_project_role(
                    self.project.id, f.user, role)
        return self.project


class DownloadForm(forms.Form):
    CHOICES = (('all', 'All data'), ('xls', 'XLS'), ('shp', 'SHP'),
               ('res', 'Resources'))
    type = forms.ChoiceField(choices=CHOICES, initial='xls')

    def __init__(self, project, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user

    def get_file(self):
        t = round(time.time() * 1000)

        file_name = '{}-{}-{}'.format(self.project.id, self.user.id, t)
        type = self.cleaned_data['type']

        if type == 'shp':
            e = ShapeExporter(self.project)
            path, mime = e.make_download(file_name + '-shp')
        elif type == 'xls':
            e = XLSExporter(self.project)
            path, mime = e.make_download(file_name + '-xls')
        elif type == 'res':
            e = ResourceExporter(self.project)
            path, mime = e.make_download(file_name + '-res')
        elif type == 'all':
            res_exporter = ResourceExporter(self.project)
            xls_exporter = XLSExporter(self.project)
            shp_exporter = ShapeExporter(self.project)
            path, mime = res_exporter.make_download(file_name + '-res')
            data_path, _ = xls_exporter.make_download(file_name + '-xls')
            shp_path, _ = shp_exporter.make_download(file_name + '-shp')

            with ZipFile(path, 'a') as myzip:
                myzip.write(data_path, arcname='data.xlsx')
                myzip.write(shp_path, arcname='data-shp.zip')
                myzip.close()

        return path, mime


class SelectImportForm(forms.Form):
    MIME_TYPES = {
        'xls': [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ],
        'csv': [
            'text/csv'
        ]
    }
    MAX_FILE_SIZE = 512000
    TYPE_CHOICES = (('xls', 'XLS'), ('shp', 'SHP'),
                    ('csv', 'CSV'))
    ENTITY_TYPE_CHOICES = (('SU', 'Locations'), ('PT', 'Parties'))

    name = forms.CharField(required=True, max_length=200)
    type = forms.ChoiceField(
        choices=TYPE_CHOICES, initial='csv', widget=forms.RadioSelect)
    entity_types = forms.MultipleChoiceField(
        choices=ENTITY_TYPE_CHOICES, widget=forms.CheckboxSelectMultiple(),
        required=False, initial=[choice[0] for choice in ENTITY_TYPE_CHOICES])
    file = forms.FileField(required=True)
    description = forms.CharField(
        required=False, max_length=2500, widget=forms.Textarea)
    mime_type = forms.CharField(required=False,
                                max_length=200,
                                widget=forms.HiddenInput)
    original_file = forms.CharField(required=False,
                                    max_length=200,
                                    widget=forms.HiddenInput)
    is_resource = forms.BooleanField(
        required=False, initial=True, widget=forms.CheckboxInput)

    def __init__(self, project, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user

    def clean_file(self):
        file = self.cleaned_data.get("file", False)
        if file.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                _('File too large, max size 512kb'))
        return file

    def clean_mime_type(self):
        file = self.cleaned_data.get("file", False)
        type = self.cleaned_data.get("type", None)
        if file and type:
            mime_type = mimetypes.guess_type(file.name)[0]
            types = self.MIME_TYPES.get(type)
            if mime_type not in types:
                self.add_error('file', _("Invalid file type"))
            return mime_type

    def clean_original_file(self):
        file = self.cleaned_data.get("file", False)
        if file:
            return file.name

    def clean_entity_types(self):
        entity_types = self.cleaned_data.get('entity_types', None)
        if entity_types is None or len(entity_types) == 0:
            self.add_error(
                'entity_types', _('Select at least one data type.')
            )
        else:
            return entity_types


class MapAttributesForm(forms.Form):
    attributes = forms.MultipleChoiceField(required=False)
    extra_headers = forms.CharField(required=False)

    def __init__(self, project, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user


class SelectDefaultsForm(forms.Form):
    party_type_field = forms.CharField(required=False)
    party_name_field = forms.CharField(required=False)
    location_type_field = forms.CharField(required=False)
    geometry_field = forms.CharField(required=False)

    def __init__(self, project, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.user = user

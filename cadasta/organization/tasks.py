from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from rest_framework_tmp_scoped_token import TokenManager

from tasks.celery import app


@app.task(name='export.project')
def export(org_slug, project_slug, api_key, output_type):
    pass


def schedule_project_export(project, user, output_type):
    org_slug = project.organization.slug
    prj_slug = project.slug
    endpoint = reverse(
        'api:v1:organization:project_detail',
        kwargs={'organization': org_slug, 'project': prj_slug})
    token = TokenManager(
        user=user,
        endpoints={'GET': [endpoint]},
        max_age=60 * 60 * 12,  # 12 hr expiration,
        recipient='export-service')
    token = token.generate_token()

    payload = {
        'org_slug': org_slug,
        'project_slug': prj_slug,
        'api_key': token,
        'output_type': output_type,
    }
    return export.apply_async(
        kwargs=payload,
        creator_id=user.id,
        related_content_type_id=ContentType.objects.get_for_model(project).id,
        related_object_id=project.id
    )

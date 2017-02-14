import json
import os
import requests
import subprocess
import time

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from django.views.generic.base import View
from rest_framework.views import APIView
from rest_framework.response import Response
from urllib.parse import quote as url_quote

from jsonattrs.models import Schema
from tutelary import mixins as tmixins

from organization import messages as org_messages
from organization.views.mixins import ProjectMixin
from spatial.models import SpatialUnit
from spatial.choices import TYPE_CHOICES as SPATIAL_TYPE_CHOICES
from party.models import Party, TenureRelationship, TenureRelationshipType
from resources.models import Resource
from ..export.all import AllExporter
from ..export.resource import ResourceExporter
from ..export.shape import ShapeExporter
from ..export.xls import XLSExporter

api_url = (
    settings.ES_SCHEME + '://' + settings.ES_HOST + ':' + settings.ES_PORT)
spatial_type_choices = {c[0]: c[1] for c in SPATIAL_TYPE_CHOICES}
party_type_choices = {c[0]: c[1] for c in Party.TYPE_CHOICES}


class Search(tmixins.APIPermissionRequiredMixin, ProjectMixin, APIView):

    permission_required = 'project.view_private'

    def get_perms_objects(self):
        return [self.get_project()]

    def post(self, request, *args, **kwargs):
        query = request.data.get('q')
        start_idx = int(request.data.get('start', 0))
        page_size = int(request.data.get('length', 10))
        dataTablesDraw = int(request.data['draw'])

        results_as_html = []
        num_hits = 0
        timestamp = ''

        if query:
            raw_results = self.query_es(
                self.get_project().id, query, start_idx, page_size)
            if raw_results is None:
                return Response({
                    'draw': dataTablesDraw,
                    'recordsTotal': 0,
                    'recordsFiltered': 0,
                    'data': [],
                    'error': 'unavailable',
                })

            num_hits = min(raw_results['hits']['total'],
                           settings.ES_MAX_RESULTS)
            results = raw_results['hits']['hits']

            if len(results) == 0:
                timestamp = self.query_es_timestamp(self.get_project().id)
            else:
                timestamp = results[0]['_source'].get('@timestamp')

            for result in results:
                if result['_type'] == 'project':
                    continue
                augmented_result = self.augment_result(result)
                if augmented_result is None:
                    continue
                html = self.htmlize_result(augmented_result)
                results_as_html.append([html])

        return Response({
            'draw': dataTablesDraw,
            'recordsTotal': num_hits,
            'recordsFiltered': num_hits,
            'data': results_as_html,
            'timestamp': timestamp,
        })

    def query_es(self, project_id, query, start_idx, page_size):
        """Queries the ES API based on the UI query string and returns the
        raw ES JSON results."""
        body = {
            'query': {
                'simple_query_string': {
                    'default_operator': 'and',
                    'query': query,
                }
            },
            'from': start_idx,
            'size': page_size,
            'sort': {'_score': {'order': 'desc'}},
        }
        r = requests.post('{}/project-{}/_search/'.format(api_url, project_id),
                          data=json.dumps(body, sort_keys=True),
                          headers={'content-type': 'application/json'})
        if r.status_code == 200:
            return r.json()
        else:
            return None

    def query_es_timestamp(self, project_id):
        """Queries the ES API project type to get the index timestamp."""
        r = requests.get(
            '{}/project-{}/project/_search/?q=*'.format(api_url, project_id))
        if r.status_code == 200:
            return r.json()['hits']['hits'][0]['_source'].get('@timestamp')
        else:
            return _("unknown")

    def augment_result(self, result):
        """Returns an augmented data suitable for plugging into HTML
        given the raw ES result."""
        es_type = result['_type']
        source = result['_source']
        entity = self.get_entity(es_type, source)
        if entity is None:
            return None
        model = type(entity)

        augmented_result = {
            'entity_type': entity.ui_class_name,
            'url': entity.get_absolute_url(),
            'main_label': self.get_main_label(model, source),
            'attributes': self.get_attributes(entity, source),
        }
        if model == Resource:
            augmented_result['image'] = entity.thumbnail

        return augmented_result

    def get_entity(self, es_type, source):
        """Returns the model instance for a search result given its ES type and
        the result source document, which should contain the database ID."""
        mappings = {
            'spatial': (
                {
                    'model': SpatialUnit,
                    'id_field_name': 'id',
                },
            ),
            'party': (
                {
                    'model': TenureRelationship,
                    'id_field_name': 'tenure_id',
                },
                {
                    'model': Party,
                    'id_field_name': 'id',
                },
            ),
            'resource': (
                {
                    'model': Resource,
                    'id_field_name': 'id',
                },
            ),
        }
        mapping = mappings.get(es_type)
        if mapping:
            for model_map in mapping:
                id = source.get(model_map['id_field_name'])
                if id:
                    try:
                        return model_map['model'].objects.get(id=id)
                    except ObjectDoesNotExist:
                        pass
        return None

    def get_main_label(self, model, source):
        """Returns the search result's main UI label."""
        if model == SpatialUnit:
            return spatial_type_choices.get(source['type'], '—')
        elif model == TenureRelationship:
            try:
                rel_type = TenureRelationshipType.objects.get(
                    id=source['tenure_type_id'])
                return _(rel_type.label)
            except TenureRelationshipType.DoesNotExist:
                return '—'
        else:  # Party or Resource
            return source.get('name', '—')

    def get_attributes(self, entity, source):
        """Returns additional display data for the result."""
        if type(entity) == SpatialUnit:
            attributes = []
            schema = Schema.objects.from_instance(entity)
            attrs = [a for s in schema for a in s.attributes.all()]
            attributes.extend([
                (a.long_name, a.render(entity.attributes.get(a.name, '—')))
                for a in attrs if not a.omit and 'name' in a.name
            ])
        elif type(entity) == Party:
            label = party_type_choices.get(source.get('type'), '—')
            attributes = [(_("Type"), label)]
        elif type(entity) == TenureRelationship:
            attributes = [
                (_("Party"), source.get('name')),
                (_("Location type"), entity.spatial_unit.name),
            ]
        else:  # Resource
            attributes = [
                (_("Original file"), source.get('original_file')),
                (_("Description"), source.get('description', '—')),
            ]
        return attributes

    def htmlize_result(self, result):
        """Formats the search result into an HTML snippet."""
        return render_to_string(
            'search/search_result_item.html', {'result': result})


class SearchExport(tmixins.PermissionRequiredMixin, ProjectMixin, View):

    permission_required = 'project.download'
    permission_denied_message = org_messages.PROJ_DOWNLOAD
    raise_exception = True

    exporters = {
        'shp': ShapeExporter,
        'xls': XLSExporter,
        'res': ResourceExporter,
        'all': AllExporter,
    }

    def get_perms_objects(self):
        return [self.get_project()]

    def post(self, request, *args, **kwargs):
        query = request.POST.get('q')
        export_format = request.POST.get('type')
        if not query or export_format not in self.exporters.keys():
            return HttpResponseBadRequest()

        project = self.get_project()
        es_dump_path = self.query_es(project.id, request.user.id, query)
        exporter = self.exporters[export_format](project)
        path, mime_type = exporter.make_download(es_dump_path)

        ext = os.path.splitext(path)[1]
        response = HttpResponse(open(path, 'rb'), content_type=mime_type)
        response['Content-Disposition'] = ('attachment; filename=' +
                                           project.slug + ext)
        return response

    def query_es(self, project_id, user_id, query):
        """Run a curl command to ES and dump the results into a temp file."""

        query_dsl = {
            'query': {
                'simple_query_string': {
                    'default_operator': 'and',
                    'query': query,
                }
            },
            'from': 0,
            'size': settings.ES_MAX_RESULTS,
            'sort': {'_score': {'order': 'desc'}},
        }
        query_dsl_param = url_quote(json.dumps(query_dsl), safe='')
        t = round(time.time() * 1000)
        es_dump_path = os.path.join(
            settings.MEDIA_ROOT,
            'temp/{}-{}-{}.esjson'.format(project_id, user_id, t)
        )
        subprocess.run([
            'curl',
            '-o', es_dump_path,
            '-XGET',
            '{}/project-{}/_data/?format=json&source={}'.format(
                api_url, project_id, query_dsl_param
            )
        ])
        return es_dump_path

import requests
import json

from django.conf import settings
from django.utils.translation import ugettext as _
from django.core.exceptions import ObjectDoesNotExist

from rest_framework.views import APIView
from rest_framework.response import Response
from tutelary.mixins import APIPermissionRequiredMixin
from jsonattrs.models import Schema

from organization.views.mixins import ProjectMixin
from spatial.models import SpatialUnit
from spatial.choices import TYPE_CHOICES as SPATIAL_TYPE_CHOICES
from party.models import Party, TenureRelationship, TENURE_RELATIONSHIP_TYPES
from resources.models import Resource


api = settings.ES_SCHEME + '://' + settings.ES_HOST + ':' + settings.ES_PORT


class Search(APIPermissionRequiredMixin,
             ProjectMixin,
             APIView):

    permission_required = 'project.view_private'

    def get_perms_objects(self):
        return [self.get_project()]

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('q')
        results_as_html = []
        timestamp = ''

        if query:
            raw_results = self.query_es(query, self.get_project().id)
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
                results_as_html.append([
                    augmented_result['entity_type'],  # Column for filtering
                    augmented_result['main_label'],   # Column for sorting
                    html,                             # Column for display
                ])

        return Response({
            'results': results_as_html,
            'timestamp': timestamp,
        })

    def query_es(self, query, project_id):
        """Queries the ES API based on the UI query string and returns the
        raw ES JSON results."""
        body = {
            'query': {
                'simple_query_string': {
                    'default_operator': 'and',
                    'query': query,
                }
            }
        }
        r = requests.post('{}/project-{}/_search'.format(api, project_id),
                          data=json.dumps(body, sort_keys=True))
        assert r.status_code == 200
        return r.json()

    def query_es_timestamp(self, project_id):
        """Queries the ES API project type to get the index timestamp."""
        r = requests.get(
            '{}/project-{}/project/_search?q=*'.format(api, project_id))
        assert r.status_code == 200
        return r.json()['hits']['hits'][0]['_source'].get('@timestamp')

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
            'url': entity.ui_detail_url,
            'main_label': self.get_main_label(model, source),
            'attributes': self.get_attributes(entity, source),
        }
        if model == Resource:
            augmented_result['image'] = entity.thumbnail

        return augmented_result

    def get_entity(self, es_type, source):
        """Returns the model instance for a search result given its ES type and
        the result source document, which should contain the database ID."""
        mappings = (
            ('spatial', (
                (SpatialUnit, 'id'),)),
            ('party', (
                (TenureRelationship, 'tenure_id'),
                (Party, 'id'))),
            ('resource', (
                (Resource, 'id'),)),
        )
        for mapping in mappings:
            if es_type == mapping[0]:
                for model_map in mapping[1]:
                    id = source.get(model_map[1])
                    if id:
                        try:
                            return model_map[0].objects.get(id=id)
                        except ObjectDoesNotExist:
                            pass
        return None

    def get_main_label(self, model, source):
        """Returns the search result's main UI label."""
        if model == SpatialUnit:
            for key, item in SPATIAL_TYPE_CHOICES:
                if key == source['type']:
                    return item
        elif model == TenureRelationship:
            for key, item in TENURE_RELATIONSHIP_TYPES:
                if key == source['tenure_type_id']:
                    return item
        else:  # Party or Resource
            return source.get('name', '—')

        # If nothing matched somehow
        return '—'

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
            label = '—'
            for key, item in Party.TYPE_CHOICES:
                if key == source.get('type'):
                    label = item
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
        html = (
            '<div class="search-result-item">'
            '<h4><span class="small">{entity_type}</span> '
            '<a href="{url}">{main_label}</a></h4>'
        ).format(
            entity_type=result['entity_type'],
            url=result['url'],
            main_label=result['main_label'],
        )
        if result.get('image'):
            html += (
                '<img src="{image}" class="thumb-60 pull-left">'
            ).format(image=result['image'])
        html += '<table class="table entity-attributes">'
        for key, attr in result['attributes']:
            html += (
                '<tr>'
                '<td class="col-md-3"><strong>{key}</strong></td>'
                '<td class="col-md-9">{attr}</td>'
                '</tr>'
            ).format(key=key, attr=attr)
        html += '</table></div>'
        return html

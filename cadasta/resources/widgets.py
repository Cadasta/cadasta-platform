from django.utils import formats
from django.utils.translation import get_language
from django.forms import CheckboxInput
from django.template.defaultfilters import date


class ResourceWidget(CheckboxInput):
    html = (
        '<tr>'
        '  <td>{checkbox}</td>'
        '  <td>'
        '    <img src="{resource.thumbnail}" '
        '         class="thumb-60">'
        '    <label for="{name}"><strong>{resource.name}</strong></label>'
        '    <br>{resource.file_name}'
        '  </td>'
        '  <td>{resource.file_type}</td>'
        '  <td>{resource.num_entities}</td>'
        '  <td>{resource.contributor.full_name}<br>'
        '      {resource.contributor.username}</td>'
        '  <td>{date_updated}</td>'
        '</tr>'
    )

    def __init__(self, resource, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource = resource

    def render(self, name, value, attrs=None):
        date_format = formats.get_format("DATETIME_FORMAT",
                                         lang=get_language())
        checkbox = super().render(name, value, attrs=attrs)
        return self.html.format(
            name=name,
            resource=self.resource,
            checkbox=checkbox,
            date_updated=date(self.resource.last_updated, date_format)
        )

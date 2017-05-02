from django.utils import formats
from django.utils.translation import get_language, ugettext as _
from django.forms import CheckboxInput
from django.template.defaultfilters import date


class ResourceWidget(CheckboxInput):
    html = (
        '<tr>'
        '  <td>{checkbox}</td>'
        '  <td>'
        '    <div class="media-left">'
        '       <img src="{resource.thumbnail}"'
        '           class="thumb-60">'
        '    </div>'
        '    <div class="media-body resource-text">'
        '       <label for="{name}"><strong>{resource.name}</strong></label>'
        '       <br>{resource.original_file}'
        '    </div>'
        '  </td>'
        '  <td class="hidden-xs hidden-sm">{resource.file_type}</td>'
        '  <td class="hidden-xs hidden-sm">'
        '      {resource.contributor.username}<br>'
        '      {resource.contributor.full_name}</td>'
        '  <td class="hidden-xs hidden-sm">{date_updated}</td>'
        '  <td>{attachment_text}</td>'
        '</tr>'
    )

    def __init__(self, resource, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resource = resource

    def get_attachment_text(self, num_entities):
        # TODO: There should be a way to make the pluralization logic
        # localizable (maybe plural is > 2 in some locales)
        if num_entities == 0:
            return _("Unattached")
        elif num_entities == 1:
            return _("Attached to 1 other entity")
        else:
            plural_text = _("Attached to {number} other entities")
            return plural_text.format(number=num_entities)

    def render(self, name, value, attrs=None):
        date_format = formats.get_format("DATETIME_FORMAT",
                                         lang=get_language())
        checkbox = super().render(name, value, attrs=attrs)
        num_entities = self.resource.num_entities
        return self.html.format(
            name=name,
            resource=self.resource,
            checkbox=checkbox,
            date_updated=date(self.resource.last_updated, date_format),
            attachment_text=self.get_attachment_text(num_entities),
        )

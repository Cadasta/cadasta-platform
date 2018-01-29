{% load i18n %}
var {td, a} = React.DOM;
var context = {
  url: "{% url 'api:v1:party:list' project=object.slug organization=object.organization.slug %}",
  layouts: [
    {
      title: "{% trans 'Name' %}",
      columns: 3,
      orderKeyword: 'name',
      render: function(party) {
        return (
          td(null,
            a({href: party.id + '/'}, party.name),
          )
        )
      }
    },
    {
      title: "{% trans 'Type' %}",
      columns: 9,
      orderKeyword: 'type',
      render: function(resource) {
        // Populate data tags for xlang plugin
        var translations = {};
        for (var lang in resource.type_display) {
          var key = 'data-label-' + lang;
          translations[key] = resource.type_display[lang];
        }

        // Render value to current language settings
        var cur_lang = $('#form-langs-select').val();
        var translated_type_display = resource.type_display[cur_lang];
        return (
          td(translations, translated_type_display)
        )
      }
    },
  ],
  rowLink: function(resource) {
    return resource.id + '/'
  },
}

ReactDOM.render(
  React.createElement(PaginatedTable, context, null),
  document.getElementById('paginated-table')
);

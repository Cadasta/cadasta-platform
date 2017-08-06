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
      render: function(resource) {
        return (
          td(null, resource.type_display)
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

{% load i18n %}

function isLinked(resource) {
  return resource.links.find(function(link) {
    return link.id == "{{ object.id }}"
  });
}


var {div, td, img, p, a, br, strong, button, span} = React.DOM;
var context = {
  url: "{% url 'api:v1:resources:project_list' project=object.slug organization=object.organization.slug %}",
  thClasses: 'hidden-xs hidden-sm',
  layouts: [
    {
      title: "{% trans 'Resource' %}",
      columns: 4,
      orderKeyword: 'name',
      render: function(resource) {
        return (
          td(null,
            div({className: 'media-left'},
              img({src: resource.thumbnail || '', className: "thumb-60"}),
            ),
            div({className: 'media-body'},
              p(null,
                a({href: resource.id + '/'},
                  strong(null, resource.name),
                ),
                br(),
                resource.original_file,
              ),
            ),
          )
        )
      }
    },
    {
      title: "{% trans 'Type' %}",
      render: function(resource) {
        return (
          td({className: 'hidden-xs hidden-sm'},
            resource.file_type,
          )
        )
      }
    },
    {
      title: "{% trans 'Contributor' %}",
      columns: 2,
      orderKeyword: 'contributor__username',
      render: function(resource) {
        return (
          td({className: 'hidden-xs hidden-sm'},
            resource.contributor.username,
            br(),
            resource.contributor.full_name,
          )
        )
      }
    },
    {
      title: "{% trans 'Last Updated' %}",
      columns: 2,
      orderKeyword: 'last_updated',
      render: function(resource) {
        return (
          td({className: 'hidden-xs hidden-sm'},
            moment(resource.last_updated).format('lll'),
          )
        )
      }
    },
    {
      title: "{% trans 'Attached to' %}",
      columns: 2,
      render: function(resource) {
        var text = isLinked(resource) ?
          (resource.links.length - 1) + " {% trans 'other' %}" :
          resource.links.length || "{% trans 'Unattached' %}"
        return (
          td({className: 'hidden-xs hidden-sm'},
            text,
          )
        )
      }
    },
    {
      render: function(resource) {

        /**
         * Generate optional button for resource
         * @param  {Object} resource Resource data
         * @return {DOMElement}      Button to be rendered
         */
        function getButton(resource) {
          if (isLinked(resource)) {
            var removeOpts = {
              className: 'btn btn-danger btn-sm',
              ariaHidden: true,
              onClick: function(e) {
                // Prevent the row-click event handler
                e.stopPropagation();

                var uri = resource.id + '/detach/' + link.link_id;
                uri = uri + "/?next={{ request.path }}";
                var form = $('<form method="POST">').attr('action', uri);
                form.append($("{% csrf_token %}"))
                $(document.body).append(form);
                form.submit();
              }
            }
            return (
              button(removeOpts,
                span({className: "glyphicon glyphicon-remove", ariaHidden: true}),
                "{% trans 'Detach' %}",
              )
            )
          }

          if (resource.archived) {
            var restoreOpts = {
              className: 'btn btn-default btn-sm restore',
              ariaHidden: true,
              onClick: function(e) {
                // Prevent the row-click event handler
                e.stopPropagation();

                var unarchiveUrl = resource.id + '/unarchive/'
                $('#undelete_resource_confirm .modal-footer a')
                  .attr('href', unarchiveUrl + '?next=' + window.location.pathname)
                $('#undelete_resource_confirm').modal()
              }
            }
            return (
              button(restoreOpts,
                "{% trans 'Restore' %}",
              )
            )
          }
        }

        return (
          td({className: "text-right"}, getButton(resource))
        )
      }
    }
  ],
  rowLink: function(resource) {
    return resource.id + '/'
  },
}

ReactDOM.render(
  React.createElement(PaginatedTable, context, null),
  document.getElementById('paginated-table')
);

'use strict';
(function(window, document, $) {
  $(document).on('init.dt', function(e) {

    if ( e.namespace !== 'dt' ) {
      return;
    }

    var addSelectOptions = function(){
      var options = [
        { value: 'archived-False', label: gettext('Active'  ) },
        { value: 'archived-True' , label: gettext('Archived') },
        { value: ''              , label: gettext('All'     ) },
      ];
      var html = '<select class="form-control input-sm" id="archive-filter">';
      for (var i = 0; i < options.length; i++) {
        html += '<option value="' + options[i].value + '">' + options[i].label + '</option>';
      }
      html += '</select>';
      var selectOptions = document.createElement('label');
      selectOptions.innerHTML = html;
      return selectOptions;
    }

    // When there are archived objects
    var table = $('#DataTables_Table_0').DataTable();
    var numCols = table.columns().count();
    var hasArchived = table
        .column(numCols - 1)
        .nodes()
        .filter(function(node) { return node.dataset.filter === "archived-True" })
        .length > 0;
    if (hasArchived) {

      // Add archived filter select field
      $('.dataTables_filter')[0].appendChild(addSelectOptions());

      // Register custom DataTables search function for the archived filter field
      $.fn.dataTable.ext.search.push(
        function(settings, searchData, index, rowData, counter) {
          var expected = $('#archive-filter').val()
          var actual = searchData[searchData.length - 1];
          return expected === '' || expected === actual;
        }
      );

      // Trigger refiltering when the archived filter field is changed
      $('#archive-filter').change(function() { table.draw(); });

      // Re-refresh table now that the archived filter field has been added
      table.draw();
    }
  });
})(window, document, jQuery);

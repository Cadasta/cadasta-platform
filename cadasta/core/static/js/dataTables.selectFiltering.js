'use strict';
(function(window, document, $) {
  $(document).on('init.dt', function(e, dtSettings) {

    if ( e.namespace !== 'dt' ) {
      return;
    }

    var addSelectOptions = function(){
      var options = [
        { value: 'archived-False', label: gettext('Active'  ) },
        { value: 'archived-True' , label: gettext('Archived') },
        { value: ''              , label: gettext('All'     ) },
      ];
      var html = '<label><select class="form-control input-sm" id="archive-filter">';
      for (var i = 0; i < options.length; i++) {
        html += '<option value="' + options[i].value + '">' + options[i].label + '</option>';
      }
      return html + '</select></label>';
    }

    // When there are archived objects
    if ($('td[data-filter="archived-True"]').length) {
      var table = $('#DataTables_Table_0').DataTable();

      // Add archived filter select field
      dtSettings.nTableWrapper.childNodes[0].childNodes[0].innerHTML += addSelectOptions()

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

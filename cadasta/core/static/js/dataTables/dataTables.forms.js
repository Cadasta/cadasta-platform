'use strict';

// This function should be called for any DataTable inside an HTML form that
// contains form fields. This ensures that when the form is submitted, any form
// fields that are hidden because of the DataTable paging/search/filter
// functionality is still submitted with the form.
function activateFormFieldsInDataTable(
  formSelector,  // jQuery selector for the HTML form
  columnIndex,   // column index in the DataTable that contains the form fields
  fieldType      // form field type as a string (supported: 'checkbox', 'select')
) {
  var form = $(formSelector);
  form.submit(function() {
    var cells = $(form).find('.datatable').DataTable().column(columnIndex).nodes();
    for (var i = 0; i < cells.length; i++) {
      if (!document.body.contains(cells[i])) {
        var cell = $(cells[i]);
        if (fieldType == 'select') {
          var select = cell.find('select');
          if (select.length > 0) {
            form.append('<input type="hidden" name="' + select[0].name + '" value="' + select.val() + '" />');
          }
        }
        else if (fieldType == 'checkbox') {
          var checkbox = cell.find('input[type="checkbox"]')[0];
          if (checkbox && checkbox.checked) {
            form.append('<input type="hidden" name="' + checkbox.name + '" value="on" />');
          }
        }
        else {
          console.log('activateFormFieldsInDataTable: "' + fieldType + '" is not supported.');
        }
      }
    }
    return true;
  });
}

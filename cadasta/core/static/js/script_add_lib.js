/**
Used in adding existing resource forms.
**/
$(function() {
  'use strict';
  activateFormFieldsInDataTable('.modal form', 0, 'checkbox');

  $('.modal .datatable tr').click(function(event) {
    if (event.target.type !== 'checkbox') {
      $(':checkbox', this).trigger('click');
    }
  });
});

 var dataTableHook = function(){
  $('.datatable').DataTable({
    destroy: true,
    conditionalPaging: true,
    "dom": '<"table-search clearfix"f>t<"table-entries"i><"table-num"l><"table-pagination"p>',
    "language": dataTable_language,
    "aria": dataTable_aria,
  });
  $('.dropdown-toggle').dropdown();
  $('#language').change(function() { this.form.submit(); });
  $('[data-parsley-required="true"]')
    .closest('.form-group')
      .children('label.control-label')
        .addClass('required');
};

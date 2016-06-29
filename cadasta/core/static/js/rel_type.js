$('select[name="relationship_type"]').change(function(event) {
  $('.related-object-form').addClass('hidden');
  $('#' + event.target.value).removeClass('hidden');
  if (event.target.value === 'L') {
    window.map.invalidateSize();
  }
});

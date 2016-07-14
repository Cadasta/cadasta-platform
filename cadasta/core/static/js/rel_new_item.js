$('button#add-party').click(function() {
  var val = $('#new_entity_field').val();
  $('#new_entity_field').val((val === 'on' ? '' : 'on'));
});

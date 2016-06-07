$('button#add_btn').click(function() {
  var val = $('#new_enitity_field').val();
  $('#new_enitity_field').val((val === 'on' ? '' : 'on'));
});

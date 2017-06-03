/* eslint-env jquery */
/**
When a user selects " + Add party", the add party button and party select dropdown disappear.
*/

$('button#add-party').click(function() {
  $('div#select-party').toggleClass('hidden');
  $('div#new-item').toggleClass('hidden');
  $('#new_entity_field').val('on');
});

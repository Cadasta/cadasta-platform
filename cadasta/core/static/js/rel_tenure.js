/* eslint-env jquery */

$('button#add-party').click(function() {
  $('div#select-party').toggleClass('hidden');
  $('div#new-item').toggleClass('hidden');
});

$('table#select-list tr').click(function(event) {
  const target = $(event.target).closest('tr');
  const relId = target.attr('data-id');
  target.closest('tbody').find('tr.info').removeClass('info');
  target.addClass('info');
  $('input[name="id"]').val(relId);
});

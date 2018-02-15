/* eslint-env jquery */

// hides all party type fields and disables form-control
function disableConditionals() {
  $('.party-*').addClass('hidden');
  $('.party-* .form-control').prop('disabled', true);
}

// unhides selected party type field and enables form-control
// hides other party type fields and disables form-control
function enableConditions(val) {
  const types = ['co', 'gr', 'in'];
  types.splice(types.indexOf(val), 1);
  $('.party-' + val).removeClass('hidden');
  $('.party-' + val + ' .form-control').prop('disabled', false);
  for (i in types) {
    $('.party-' + types[i]).addClass('hidden')
    $('.party-' + types[i] + ' .form-control').prop('disabled', true);
  }
}

function toggleStates(val) {
  if (val === '') {
    disableConditionals();
  } else {
    enableConditions(val);
  }
}

$().ready(function() {
  const val = $('.party-type').val().toLowerCase();
  toggleStates(val);
});

$('select.party-type').on('change', function(e) {
  const val = e.target.value.toLowerCase();
  toggleStates(val);
});

$('select.party-select').on('change', function(e) {
  toggleStates('');
});

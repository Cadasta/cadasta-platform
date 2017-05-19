/* eslint-env jquery */

function disableConditionals() {
  $('.party-co').addClass('hidden');
  $('.party-gr').addClass('hidden');
  $('.party-in').addClass('hidden');
  $('.party-co .form-control').prop('disabled', 'disabled');
  $('.party-gr .form-control').prop('disabled', 'disabled');
  $('.party-in .form-control').prop('disabled', 'disabled');
}

function enableConditions(val) {
  const types = ['co', 'gr', 'in'];
  types.splice(types.indexOf(val), 1);
  $('.party-' + val).removeClass('hidden');
  $('.party-' + val + ' .form-control').prop('disabled', '');
  for (i in types) {
    $('.party-' + types[i]).addClass('hidden')
    $('.party-' + types[i] +  '.form-control').prop('disabled', 'disabled');
  }
}

function toggleParsleyRequired(val) {
  const typeChoices = ['in', 'gr', 'co'];
  $.each(typeChoices, function(idx, choice) {
    if (val === choice) {
      $.each($('.party-' + val + ' .form-control'), function(idx, value) {
        if (value.hasAttribute('data-parsley-required')) {
          $(value).attr('data-parsley-required', true);
          $(value).prop('required', 'required');
          $(value).prev('label').addClass('required');
        }
      });
    } else {
      $.each($('.party-' + choice + ' .form-control'), function(idx, value) {
        if (value.hasAttribute('data-parsley-required')) {
          $(value).attr('data-parsley-required', false);
          $(value).prop('required', '');
          $(value).prev('label').removeClass('required');
        }
      });
    }
  });
}

function toggleStates(val) {
  if (val === '') {
    disableConditionals();
  } else {
    enableConditions(val);
    toggleParsleyRequired(val);
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

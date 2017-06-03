/* eslint-env jquery */
/**
Adds ability to toggle between conditional attributes.
If 'Individual' is selected as the party type, individual attributes will be displayed.
If 'Group' is selected, individual will disappear and group attributes will be displayed.
**/

function disableConditionals() {
  $('.party-co').addClass('hidden');
  $('.party-gr').addClass('hidden');
  $('.party-in').addClass('hidden');
  $('.party-co .form-control').prop('disabled', 'disabled');
  $('.party-gr .form-control').prop('disabled', 'disabled');
  $('.party-in .form-control').prop('disabled', 'disabled');
}

function enableConditions(val) {
  var types = ['co', 'gr', 'in'];
  types.splice(types.indexOf(val), 1);
  $('.party-' + val).removeClass('hidden');
  $('.party-' + val + ' .form-control').prop('disabled', '');
  for (var i in types) {
    $('.party-' + types[i]).addClass('hidden');
    $('.party-' + types[i] +  '.form-control').prop('disabled', 'disabled');
  }
}

function toggleParsleyRequired(val) {
  var typeChoices = ['in', 'gr', 'co'];
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
  var val = $('.party-type').val().toLowerCase();
  toggleStates(val);
});


$('select.party-type').on('change', function(e) {
  var val = e.target.value.toLowerCase();
  toggleStates(val);
});

$('select.party-select').on('change', function(e) {
  toggleStates('');
});

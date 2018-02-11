/*
    Client-side form validation for fields
*/

// PHONE NUMBER CUSTOM VALIDATORS

  // checks phone number starts with a plus
  window.Parsley
    .addValidator('phoneplus', function(value, requirement) {
      var regex = new RegExp("^[+]");
      var check = + regex.test(value);
      if (check < 1) {
        return false;
      }
    }, 1006)
    .addMessage('phoneplus', gettext('Your phone number must start with +.'));

  // checks phone number is between 5 and 15 digits
  window.Parsley
    .addValidator('phonelength', function(value, requirement) {
      var regex = new RegExp("^[+][0-9]{5,14}$");
      var check = + regex.test(value);
      if (check < 1) {
        return false;
      }
    }, 1005)
    .addMessage('phonelength', gettext('Your phone number must contain between 5 and 15 digits without spaces or punctuation.'));

  // checks country code and phone number is valid
  window.Parsley
    .addValidator('phonenumber', function(value, requirement) {
      if (!libphonenumber.isValidNumber(value)) {
        return false;
      }
    }, 1004)
    .addMessage('phonenumber', gettext('Your country code and phone number is not valid.'));

// PASSWORD CUSTOM VALIDATORS

  // checks password 3 out of 4 character requirement
  window.Parsley
    .addValidator('character', function (value, requirement) {
      var isNumeric = + /\d+/.test(value),
        isCapitals  = + /[A-Z]+/.test(value),
        isSmall     = + /[a-z]+/.test(value),
        isSpecial   = + /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/.test(value);
      if (isNumeric + isCapitals  + isSmall + isSpecial < requirement) {
        return false;
      }
    }, 1003)
    .addMessage('character', gettext('Your password must contain at least 3 of the following: lowercase characters, uppercase characters, special characters, and/or numerical characters.'));

  // checks username not contained in password when username is another field in form
  window.Parsley
    .addValidator('userfield', function (value, requirement) {
      var term = $("#id_username").val();
      if (term.length && value.indexOf(term) >= 0) {
        return false;
      }
    }, 1002)
    .addMessage('userfield', gettext('Your password cannot contain your username.'));

  // checks email not contained in password when email is another field in form
  window.Parsley
    .addValidator('emailfield', function (value, requirement) {
      var term = $("#id_email").val().split("@");
      if (term[0].length && value.indexOf(term[0]) >= 0) {
        return false;
      }
    }, 1001)
    .addMessage('emailfield', gettext('Your password cannot contain your email mailbox name.'));

  // checks phone number not contained in password
  window.Parsley
    .addValidator('phonefield', function (value, requirement) {
      var term = libphonenumber.parse($("#id_phone").val());
      if ('phone' in term) {
        var originalString = libphonenumber.format(term, 'International');
        var splitString = originalString.split(" ");
        var phonematch = (splitString.slice(2)).join('');
        if (value.indexOf(phonematch) >= 0) {
            return false;
        }
      }
    }, 1000)
    .addMessage('phonefield', gettext('Your password cannot contain your phone number.'));

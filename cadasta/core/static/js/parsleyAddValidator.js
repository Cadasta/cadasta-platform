/*
    Client-side form validation for fields
*/

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
    }, 3)
    .addMessage('character', gettext('Your password must contain at least 3 of the following: lowercase characters, uppercase characters, special characters, and/or numerical characters.'));

  // checks username not contained in password when username is another field in form
  window.Parsley
    .addValidator('userfield', function (value, requirement) {
      var term = $("#id_username").val();
      if (term.length && value.indexOf(term) >= 0) {
        return false;
      }
    }, 2)
    .addMessage('userfield', gettext('Your password cannot contain your username.'));

  // checks email not contained in password when email is another field in form
  window.Parsley
    .addValidator('emailfield', function (value, requirement) {
      var term = $("#id_email").val().split("@");
      if (term[0].length && value.indexOf(term[0]) >= 0) {
        return false;
      }
    }, 2)
    .addMessage('emailfield', gettext('Your password cannot contain your email mailbox name.'));

  // checks phone number starts with a plus followed by 0-9 numbers
  window.Parsley
    .addValidator('phoneplus', function(value, requirement) {
      var term = $("#id_phone").val();
      var checkLength = ((term.length)-1);
      var regex = new RegExp("[+]([0-9]){" + checkLength + "}");
      var check = + regex.test(value);
      if (check < 1) {
        return false;
      }
    }, 2)
    .addMessage('phoneplus', gettext('Your phone number must start with +, followed by a country code and phone number with no spaces or punctuation.'));

  // checks phone number length is between min and exceed max length
  window.Parsley
    .addValidator('phonelength', function (value, requirement) {
      var term = $("#id_phone").val();
      if ((term.length < 6)||(term.length > requirement)) {
        return false;
      }
    }, 1)
    .addMessage('phonelength', gettext('Your phone number must contain between 5 and 14 digits.'));


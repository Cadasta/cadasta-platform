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

  // checks phone number starts with a plus
  window.Parsley
    .addValidator('phoneplus', function(value, requirement) {
      var regex = new RegExp("^[+]");
      var check = + regex.test(value);
      if (check < 1) {
        return false;
      }
    }, 3)
    .addMessage('phoneplus', gettext('Your phone number must start with +.'));

  // checks phone number has between 6 and 15 characters
  window.Parsley
    .addValidator('phonelength', function(value, requirement) {
      var check = value.length;
      if ((check < 6) || (check > requirement)) {
        return false;
      }
    }, 2)
    .addMessage('phonelength', gettext('Your phone number must have between 5 and 15 digits.'));

  // checks phone number is all numbers without spaces or punctuation
  window.Parsley
    .addValidator('phonenumber', function(value, requirement) {
      var regex = new RegExp("[+]([0-9]*$)");
      var check = + regex.test(value);
      if (check < 1) {
        return false;
      }
    }, 1)
    .addMessage('phonenumber', gettext('Your phone number must start with +, followed by a country code and phone number without spaces or punctuation. '));



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
      console.log(term)
      if (value.indexOf(term) >= 0) {
        return false;
      }
    }, 2)
    .addMessage('userfield', gettext('BLAHHHHH Your password cannot contain your username.'));

  // checks email not contained in password when email is another field in form
  window.Parsley
    .addValidator('emailfield', function (value, requirement) {
      var term = $("#id_email").val().split("@");
      if (value.indexOf(term[0]) >= 0) {
        return false;
      }
    }, 2)
    .addMessage('emailfield', gettext('Your password cannot contain your email mailbox name.'));

$(document).ready(function() {
  $("#phone-btn").click(function(){
      $("#phone-div").removeClass("hidden");
      $("#email-div").addClass("hidden");
      $('#id_phone').attr('data-parsley-required', 'true');
      $('#id_email').attr('data-parsley-required', 'false');
      document.getElementById("id_email").value='';
      $('#id_email').parsley().reset();
      sessionStorage.setItem('phone',"true");
      sessionStorage.removeItem('email', null);

  });
  $("#email-btn").click(function(){
      $("#email-div").removeClass("hidden");
      $("#phone-div").addClass("hidden");
      $('#id_phone').attr('data-parsley-required', 'false');
      $('#id_email').attr('data-parsley-required', 'true');
      document.getElementById("id_phone").value='';
      $('#id_phone').parsley().reset();
      sessionStorage.setItem('email',"true");
      sessionStorage.removeItem('phone', null);
  });
});

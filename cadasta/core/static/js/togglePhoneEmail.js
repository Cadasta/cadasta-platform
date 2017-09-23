$(document).ready(function() {
  $("#phone-btn").click(function(){
      $("#phone-div").removeClass("hidden");
      $("#email-div").addClass("hidden");
      $('#id_phone').attr('data-parsley-required', 'true');
      $('#id_email').attr('data-parsley-required', 'false');
      $('#id_email').parsley().reset();
      document.getElementById("id_email").value='';
  });
  $("#email-btn").click(function(){
      $("#email-div").removeClass("hidden");
      $("#phone-div").addClass("hidden");
      $('#id_phone').attr('data-parsley-required', 'false');
      $('#id_email').attr('data-parsley-required', 'true');
      $('#id_phone').parsley().reset();
      document.getElementById("id_phone").value='';
  });
});

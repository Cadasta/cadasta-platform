$(document).ready(function() {
  $("#phone-btn").click(function(){
      $("#phone-div").removeClass("hidden");
      $("#email-div").addClass("hidden");
      document.getElementById("id_email").value='';
  });
  $("#email-btn").click(function(){
      $("#email-div").removeClass("hidden");
      $("#phone-div").addClass("hidden");
      document.getElementById("id_phone").value='';
  });
});

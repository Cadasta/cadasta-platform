$(document).ready(function () {
  $("input[type='password'] + span > button").click(function() {
    var glyph = $(this).children(".glyphicon");
    if(glyph.hasClass("glyphicon-eye-close")) {
      $(this).parent().prev("input").attr("type", "text");
      glyph.removeClass("glyphicon-eye-close").addClass("glyphicon-eye-open");
    }
    else {
      $(this).parent().prev("input").attr("type", "password");
      glyph.removeClass("glyphicon-eye-open").addClass("glyphicon-eye-close");
    }
  });
});

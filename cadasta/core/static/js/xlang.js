/** 
For the language-dropdown in the Project Dashboard.
When questionnaires have multiple languages, users are able to choose which language to display.
**/

$(document).ready(function () {
  var storage_key = 'form_lang::' + $('#form-langs-select').attr('data-project-slug');
  function setLabels(lang) {
    var labels = $('label, option, td, a, div');

    for (var i = 0, l = labels.length; i < l; i++) {
      var label = $(labels[i]);
      var new_text = label.attr('data-label-' + lang);
      if (new_text) {
        label.text(new_text);
      }
    }
  }

  $('#form-langs-select').change(function() {
    var new_lang = $(this).val();
    localStorage.setItem(storage_key, new_lang);
    setLabels(new_lang);
  });

  var form_lang = localStorage.getItem(storage_key);
  if (form_lang && $('#form-langs-select option[value="' + form_lang + '"]').length) {
    $('#form-langs-select').val(form_lang);
    setLabels(form_lang);
  } else {
    var default_lang = $('#form-langs-select').attr('data-default-lang');
    $('#form-langs-select').val(default_lang);
    localStorage.setItem(storage_key, default_lang);
    setLabels(default_lang);
  }
});

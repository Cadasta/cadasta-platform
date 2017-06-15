/** 
For the language-dropdown in the Project Dashboard.
When questionnaires have multiple languages, users are able to choose which language to display.
**/

function xLang () {
  return {
    setLabels: function (lang) {
      var labels = $('label, option, td, a, div');

      for (var i = 0, l = labels.length; i < l; i++) {
        var label = $(labels[i]);
        var new_text = label.attr('data-label-' + lang);
        if (new_text) {
          label.text(new_text);
        }
      }
    },

    getFormLang: function () {
      var storage_key = 'form_lang::' + $('#form-langs-select').attr('data-project-slug');
      var form_lang = localStorage.getItem(storage_key);

      if (form_lang && $('#form-langs-select option[value="' + form_lang + '"]').length) {
        $('#form-langs-select').val(form_lang);
        this.setLabels(form_lang);
      } else {
        var default_lang = $('#form-langs-select').attr('data-default-lang');
        $('#form-langs-select').val(default_lang);
        localStorage.setItem(storage_key, default_lang);
        this.setLabels(default_lang);
      }
    },
  }
}


$(document).ready(function () {
  var xl = xLang();
  var storage_key = 'form_lang::' + $('#form-langs-select').attr('data-project-slug');

  $('#form-langs-select').change(function() {
    var new_lang = $(this).val();
    localStorage.setItem(storage_key, new_lang);
    xl.setLabels(new_lang);
  });

  xl.getFormLang();
});

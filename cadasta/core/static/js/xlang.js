$(document).ready(function () {
  function setLabels(lang) {
    const labels = $('label, option, td, a, div');

    for (var i = 0, l = labels.length; i < l; i++) {
      const label = $(labels[i]);
      const new_text = label.attr('data-label-' + lang)
      if (new_text) {
        label.text(new_text);
      }
    }
  }

  $('#form-langs-select').change(function() {
    const new_lang = $(this).val();
    localStorage.setItem("form_lang", new_lang);
    setLabels(new_lang);
  });

  const form_lang = localStorage.getItem("form_lang");
  if (form_lang && $('#form-langs-select option[value="' + form_lang + '"]').length) {
    $('#form-langs-select').val(form_lang);
    setLabels(form_lang);
  }
});

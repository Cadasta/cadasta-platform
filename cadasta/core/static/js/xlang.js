$(document).ready(function () {
  const storage_key = 'form_lang::' + $('#form-langs-select').attr('data-project-slug')
  function setLabels(lang) {
    const labels = $('label, option, td, a, div, span');

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
    localStorage.setItem(storage_key, new_lang);
    setLabels(new_lang);
  });

  const form_lang = localStorage.getItem(storage_key);
  if (form_lang && $('#form-langs-select option[value="' + form_lang + '"]').length) {
    $('#form-langs-select').val(form_lang);
    setLabels(form_lang);
  } else {
    const default_lang = $('#form-langs-select').attr('data-default-lang');
    $('#form-langs-select').val(default_lang);
    localStorage.setItem(storage_key, default_lang);
    setLabels(default_lang);
  }
});

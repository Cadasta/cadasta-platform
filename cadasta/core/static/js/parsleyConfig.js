// configure parsley for bootstrap 3 forms
window.ParsleyConfig = {
  errorClass: 'has-error',
  successClass: 'has-success',
  classHandler: function(ParsleyField) {
      return ParsleyField.$element.parents('.form-group');
  },
  errorsContainer: function(ParsleyField) {
      return ParsleyField.$element.parents('.form-group');
  }
};

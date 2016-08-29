$(function() {
  original_file = $('input[name="original_file"]').val();

  if (original_file) {
    $('a.file-link').text(original_file);
    $('a.file-link').attr('download', original_file);
  }

  $('.file-input').change(function(event) {
    var file = event.target.files[0];

    $('a.file-link').on('link:update', function() {
        $('a.file-link').text(file.name);
        $('a.file-link').attr('download', file.name);
    });

    $('input[name="original_file"]').val(file.name);
    $('input[name="details-original_file"]').val(file.name);
    $('input[name="mime_type"]').val(file.type);

    // import wizard
    $('input[name="select_file-original_file"]').val(file.name);
    $('input[name="select_file-mime_type"]').val(file.type);

  });

});

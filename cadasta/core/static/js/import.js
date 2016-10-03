$('input[name="select_file-file"]').change(function(event){
    var file = event.target.files[0];
    $('input[name="select_file-mime_type"]').val(file.type);
});

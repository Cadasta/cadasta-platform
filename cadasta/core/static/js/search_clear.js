$(document).ready(function() {
    function tog(v) { 
            return v?'addClass':'removeClass';
        }
    $(document).on('click input', '.clearable', function() {
        $(this)[tog(this.value)]('x');
                  }).on('mousemove', '.x', function(e) {
        $(this)[tog(this.offsetWidth-30< e.clientX-this.getBoundingClientRect().left)]('on_x');
                      }).on('touchstart click', '.on_x', function(ev) {
        ev.preventDefault();
        $(this).removeClass('x on_x').val('').change();
    });
});  
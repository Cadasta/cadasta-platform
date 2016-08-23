(function(window, document, $) {
    $(document).on('init.dt', function(e, dtSettings) {
        if ( e.namespace !== 'dt' ) {
            return;
        }
        addSelectOptions = function(){
            aData = ['Active', 'Archived', 'All']
            var r='<label><select class="form-control input-sm" id="archive-filter">', i, iLen=aData.length;
            for ( i=0 ; i<iLen ; i++ )
            {
                r += '<option value="'+aData[i]+'">'+aData[i]+'</option>';
            }
            return r+'</select></label>';
        }

        var table = $('#DataTables_Table_0').DataTable();
        table.order([1, 'asc']).draw()

        if ($(".archived").length ){
            dtSettings.nTableWrapper.childNodes[0].childNodes[0].innerHTML += addSelectOptions()
            table.columns(0).search('False').draw();

            $('input').on( 'keyup', function () {
                table.search( this.value ).draw();
            });

            $('#archive-filter').change(function () {
                var value = ''
                table.search(value).draw();
                var selection = $('#archive-filter').val()
                if (selection === 'Active') {
                    value = 'False'
                } else if (selection === 'Archived') {
                    value = 'True';
                }
                table.columns(0).search(value).draw();
            });
        }
    });
})(window, document, jQuery);
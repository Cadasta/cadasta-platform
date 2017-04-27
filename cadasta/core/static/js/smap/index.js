var map = L.map('mapid');
var editor = new LocationEditor(map);
var sr = SimpleRouter(map);
sr.router();

/*****************
EVENT LISTENERS
*****************/
window.addEventListener('hashchange', function () {
    sr.router();
});
window.addEventListener('load', function () {
    sr.router();
});
map.on('endtileload', function () {
    rm.updateState({
        'check_location_coords': true,
    });
});

SMap(map);
var hash = new L.Hash(map);

// handle location form navigation

$(document).on('click', 'a', function (e) {
    if (editor.dirty() && (editor.editing() || editor.deleting())) {
        if (e.currentTarget.hash === '#/search') return;
        if (e.currentTarget.hash === '#archive_confirm') return;
        var path = e.currentTarget.hash || e.currentTarget.href;
        if ((path && path != window.location.hash) || e.currentTarget.form) {
            e.preventDefault();
            var modal = $('#unsaved_edits').modal({
                keyboard: false,
                background: true,
            }, 'show');
            modal.one('click', '.forget-changes', function (e) {
                editor.dispose();
                modal.hide();
                editor.fire('location:reset_dirty');
                window.location.href = path;
            });
        }
    }
});

$(document).on('click', '#delete-location', function (e) {
    editor.fire('location:delete');
});

$(document).on('click', '.btn-default.cancel', function (e) {
    if (!editor.dirty()) {
        editor.fire('location:reset');
    }
});

$(document).on('click', 'button[name="submit-button"]', function (e) {
    if (editor.dirty()) {
        e.preventDefault();
        var $form = $('#location-wizard');
        var modal = $('#unsaved_edits').modal({
            keyboard: false,
            background: true,
        }, 'show');
        modal.one('click', '.forget-changes', function (e) {
            editor.cancelEdit();
            $form.trigger('submit');
            modal.hide();
        });
    }
});

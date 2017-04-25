var map = L.map('mapid');
var editor = new LocationEditor(map);
var sr = new SimpleRouter(map);
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
        if ((e.currentTarget.hash && e.currentTarget.hash != window.location.hash) || e.currentTarget.form) {
            var go = confirm('Your form has unsaved edits. Do you want to continue ? ');
            if (go) {
                editor.location._undoEdit();
                editor._resetView();
            } else {
                e.preventDefault();
            }
        }
    }
});

$(window).on('beforeunload', this, function (e) {
    if (editor.dirty() && editor.editing()) {
        return "Your form has unsaved changes."
    }
});

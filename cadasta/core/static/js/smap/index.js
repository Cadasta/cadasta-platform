var map = L.map('mapid');
var sr = new SimpleRouter(map);
sr.router();

/*****************
EVENT LISTENERS
*****************/
window.addEventListener('hashchange', function() {
    sr.router();
});
window.addEventListener('load', function() {
    sr.router();
});
map.on('endtileload', function() {
    rm.updateState({
        'check_location_coords': true,
    });
});

SMap(map);
var hash = new L.Hash(map);
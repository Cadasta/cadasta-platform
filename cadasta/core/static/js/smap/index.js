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

map.on('endloadtile', function () {
    if (!rm.getCurrentLocationLayer()) {
        rm.setCurrentLocationFeature();
    }
});


SMap(map);
var hash = new L.Hash(map);

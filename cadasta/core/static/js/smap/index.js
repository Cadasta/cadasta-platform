var map = L.map('mapid');
var sr = new SimpleRouter(map);
sr.router();
window.addEventListener('hashchange', sr.router);
window.addEventListener('load', sr.router);
SMap(map);

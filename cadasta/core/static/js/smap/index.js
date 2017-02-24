var map = L.map('mapid');
var sr = new SimpleRouter(map);
SMap(map);
sr.router();
window.addEventListener('hashchange', sr.router);
window.addEventListener('load', sr.router);

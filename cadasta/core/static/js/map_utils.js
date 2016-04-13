function geoLocate(map) {
  return function(event) {
    map.locate({ setView: true });
  }
}

function add_map_controls(map) {
  var geocoder = L.control.geocoder('search-QctWfva', {
    markers: false
  }).addTo(map);
  geocoder.on('select', function (e) {
    map.setZoomAround(e.latlng, 9);
  });

  var Geolocate = L.Control.extend({
    options: {
      position: 'topleft'
    },

    onAdd: function(map) {
      var controlDiv = L.DomUtil.create(
        'div', 'leaflet-bar leaflet-control leaflet-control-geolocate'
      );
      controlDiv.title = 'Go to my location';
      L.DomEvent
       .addListener(controlDiv, 'click', L.DomEvent.stopPropagation)
       .addListener(controlDiv, 'click', L.DomEvent.preventDefault)
       .addListener(controlDiv, 'click', geoLocate(map));

      L.DomUtil.create('span', 'glyphicon glyphicon-map-marker', controlDiv);

      return controlDiv;
    }
  });

  map.addControl(new Geolocate());
}

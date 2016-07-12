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
  return map
}

function renderFeatures(map, projectExtent, spatialUnits, trans, fitBounds) {
  var projectBounds;

  if (projectExtent) {
    var boundary = L.geoJson(
      projectExtent,
      {
        style: {
            stroke: true, 
            color: "#0e305e",
            weight: 2,
            dashArray: "5, 5",
            opacity: 1,
            fill: false
        }
      }
    );
    boundary.addTo(map);
    projectBounds = boundary.getBounds();
    if (fitBounds === 'project') {map.fitBounds(projectBounds);}
  }

  var geoJson = L.geoJson(null, {
    style: { weight: 2 },
    onEachFeature: function(feature, layer) {
      layer.bindPopup("<div class=\"text-wrap\">" +
                      "<h2><span>Location</span>" +
                      feature.properties.type + "</h2></div>" +
                      "<div class=\"btn-wrap\"><a href='" + feature.properties.url + "' class=\"btn btn-primary btn-sm btn-block\">" + trans['open'] + "</a>"  +
                      "</div>");
    }
  });

  L.Deflate(map, {minSize: 20, layerGroup: geoJson});
  geoJson.addData(spatialUnits);

  if (fitBounds === 'locations') {
    if (spatialUnits.features.length) {
      map.fitBounds(L.geoJson(spatialUnits).getBounds());
    } else if (projectBounds) {
      map.fitBounds(projectBounds);
    }
  }

  var markerGroup = L.markerClusterGroup.layerSupport()
  markerGroup.addTo(map);
  markerGroup.checkIn(geoJson);
  geoJson.addTo(map);  
}

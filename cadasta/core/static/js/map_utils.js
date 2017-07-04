function geoLocate(map) {
  return function(event) {
    map.locate({ setView: true });
  }
}

function add_map_controls(map) {
  map.removeControl(map.zoomControl);
  map.addControl(L.control.zoom({
    zoomInTitle: gettext("Zoom in"),
    zoomOutTitle: gettext("Zoom out")
  }));

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
      controlDiv.title = gettext('Go to my location');
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

function renderFeatures(map, featuresUrl, options) {
  options = options || {};

  function locationToFront() {
    if (options.location) {
      options.location.bringToFront();
    }
  }

  function loadFeatures(url) {
    $('#messages #loading').removeClass('hidden');
    $.get(url, function(response) {
      geoJson.addData(response);

      if (response.next) {
        loadFeatures(response.next, map, options.trans);
      } else {
        $('#messages #loading').addClass('hidden');
        if (options.fitBounds === 'locations') {
          var bounds = markers.getBounds();
          if (bounds.isValid()) {
            map.fitBounds(bounds);
          }
        }
      }

      locationToFront();
    });
  }

  var projectBounds;

  if (options.projectExtent) {
    var boundary = L.geoJson(
      options.projectExtent, {
        style: {
          stroke: true,
          color: "#0e305e",
          weight: 2,
          dashArray: "5, 5",
          opacity: 1,
          fill: false,
          clickable: false,
        }
      }
    );
    boundary.addTo(map);
    projectBounds = boundary.getBounds();
    if (options.fitBounds === 'project') {map.fitBounds(projectBounds);}
  } else {
    map.fitBounds([[-45.0, -180.0], [45.0, 180.0]]);
  }

  var geoJson = L.geoJson(null, {
    style: { weight: 2 },
    onEachFeature: function(feature, layer) {
      if (options.trans && options.projectUser) {
        layer.bindPopup("<div class=\"text-wrap\">" +
                      "<h2><span class=\"entity\">Location</span>" +
                      feature.properties.type + "</h2></div>" +
                      "<div class=\"btn-wrap\"><a href='" + feature.properties.url + "' class=\"btn btn-primary btn-sm btn-block\">" + options.trans['open'] + "</a>"  +
                      "</div>");
      }
    }
  });

  var markers = L.Deflate({minSize: 20, layerGroup: geoJson});
  markers.addTo(map);
  geoJson.addTo(map);

  if (options.location) {
    options.location.addTo(map);
    map.fitBounds(options.location.getBounds());
  } else if (projectBounds) {
    map.fitBounds(projectBounds);
  }
  loadFeatures(featuresUrl);
  map.on('zoomend', locationToFront);
  map.on('dragend', locationToFront);
}

function switch_layer_controls(map, options){
  // swap out default layer switcher
  var layers = options.djoptions.layers;
  var baseLayers = {};
  for (var l in layers){
    var layer = layers[l];
    var baseLayer = L.tileLayer(layer[1], layer[2]);
    baseLayers[layer[0]] = baseLayer;
  }
  // select first layer by default
  for (var l in baseLayers){
    map.addLayer(baseLayers[l]);
    break;
  }
  var groupedOptions = {
    groupCheckboxes: false
  };
  map.removeControl(map.layerscontrol);
  map.layerscontrol = L.control.groupedLayers(
    baseLayers, groupedOptions).addTo(map);
}

function add_spatial_resources(map, url){
  $.ajax(url).done(function(data){
    if (data.count == 0) return;
    var spatialResources = {};
    $.each(data.results, function (idx, resource) {
      var name = resource.name;
      var layers = {};
      $.each(resource.spatial_resources, function (i, spatial_resource) {
          var group = new L.LayerGroup();
          var layer = L.geoJson(spatial_resource.geom).addTo(group);
          layers[spatial_resource.name] = group
      });
      spatialResources[name] = layers;
    });
    $.each(spatialResources, function (sr) {
      var layers = spatialResources[sr];
      $.each(layers, function (layer) {
          map.layerscontrol.addOverlay(layers[layer], layer, sr);
      });
    });
  });
}

function enableMapEditMode() {
  var editButton = $('.leaflet-draw-edit-edit')[0];
  if (!editButton) {
    setTimeout(enableMapEditMode, 500);
  } else {
    var clickEvent = new MouseEvent('click');
    editButton.dispatchEvent(clickEvent);
  }
}

function saveOnMapEditMode() {
  var saveButton = $('.leaflet-draw-actions-top li:first-child a')[0];
  if (saveButton) {
    var clickEvent = new MouseEvent('click');
    saveButton.dispatchEvent(clickEvent);
  }
}

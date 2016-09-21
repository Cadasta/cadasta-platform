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
            fill: false,
            clickable: false,
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

  var markerGroup = L.markerClusterGroup.layerSupport();
  markerGroup.addTo(map);
  markerGroup.checkIn(geoJson);
  geoJson.addTo(map);
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
        if (data.length == 0) return;
        var spatialResources = {};
        $.each(data, function(idx, resource){
            var name = resource.name;
            var layers = {};
            var group = new L.LayerGroup();
            $.each(resource.spatial_resources, function(i, spatial_resource){
                var layer = L.geoJson(spatial_resource.geom).addTo(group);
                layers['name'] = spatial_resource.name;
                layers['group'] = group;
            });
            spatialResources[name] = layers;
        });
        $.each(spatialResources, function(sr){
            var layer = spatialResources[sr];
            map.layerscontrol.addOverlay(layer['group'], layer['name'], sr);
        })
    });
}

var SMap = (function() {
  var map = L.map('mapid');
  var layerscontrol = L.control.layers().addTo(map);

  var geojsonTileLayer = new L.TileLayer.GeoJSON(
    url, 
    {
      clipTiles: true,
      unique: function (feature) {return feature.id;}
    }, 
    {
      style: { weight: 2 },
      onEachFeature: function(feature, layer) {
        if (options.trans) {
          layer.bindPopup("<div class=\"text-wrap\">" +
                      "<h2><span>Location</span>" +
                      feature.properties.type + "</h2></div>" +
                      "<div class=\"btn-wrap\"><a href='" + feature.properties.url + "' class=\"btn btn-primary btn-sm btn-block\">" + options.trans['open'] + "</a>"  +
                      "</div>");
        }
      }
    });

  function add_tile_layers() {
    for (var i = 0, n = layers.length; i < n; i++) {
      var attrs = L.Util.extend(layers[i]['attrs']);
      var layer = {name: layers[i]['label'], url: layers[i]['url'], options: attrs};
      var l = L.tileLayer(layer.url, layer.options);
      layerscontrol.addBaseLayer(l, layer.name);

      if (i === 0) {
        l.addTo(map);
      }
    }
  }

  add_tile_layers();
  map.addLayer(geojsonTileLayer);

  function load_project_extent() {
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
      if (options.fitBounds === 'project') {
        map.fitBounds(projectBounds);
      }
    } else {
      map.fitBounds([[-45.0, -180.0], [45.0, 180.0]]);
    }
  }

  load_project_extent()

  function load_features() {;
    if (options.fitBounds === 'locations') {
      var bounds = geojsonTileLayer.geojsonLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds);
      }
    }
  }

  load_features();

  function render_spatial_resource(){
    $.ajax(fetch_spatial_resources).done(function(data){
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
        layerscontrol.addOverlay(layer['group'], layer['name'], sr);
      })
    });
  }

  render_spatial_resource();

  function geoLocate() {
    return function(event) {
      map.locate({ setView: true });
    }
  }

  $(window).on('hashchange', function() {
    if (window.location.hash === '#overview')
      $('.content-single').removeClass('detail-hidden')
    else {
        $('.content-single').addClass('detail-hidden')
    }

    window.setTimeout(function() {
      map.invalidateSize();
    }, 400);
  })
})();

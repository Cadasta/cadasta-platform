var SMap = function (map) {
    var layerscontrol = L.control.layers().addTo(map);

    var geojsonTileLayer = new L.TileLayer.GeoJSON(
        1, options.num_locations, url, {
            clipTiles: true,
            unique: function (feature) { return feature.id; }
        }, {
            style: { color: 'blue', weight: 2 },
            onEachFeature: function (feature, layer) {
                layer.on('click', function (e) {
                    map.locationEditor.onLayerClick(e);
                });
            }
        });

    function add_tile_layers() {
        for (var i = 0, n = layers.length; i < n; i++) {
            var attrs = L.Util.extend(layers[i].attrs);
            var layer = { name: layers[i].label, url: layers[i].url, options: attrs };
            var l = L.tileLayer(layer.url, layer.options);
            layerscontrol.addBaseLayer(l, layer.name);

            if (i === 0) {
                l.addTo(map);
            }
        }
    }

    add_tile_layers();
    map.addLayer(geojsonTileLayer);
    rm.setGeoJsonLayer(geojsonTileLayer);
    map.geojsonTileLayer = geojsonTileLayer;
    map.geojsonLayer = geojsonTileLayer.geojsonLayer;

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
            options.projectExtent = projectBounds;
            if (options.fitBounds === 'project') {
                map.fitBounds(projectBounds);
                return projectBounds;
            }
        } else {
            map.fitBounds([
                [-45.0, -180.0],
                [45.0, 180.0]
            ]);
        }
    }

    load_project_extent();

    /*** CURRENTLY DOES NOT WORK ***/
    function load_features() {
        if (options.fitBounds === 'locations') {
            var bounds = geojsonTileLayer.geojsonLayer.getBounds();
            if (bounds.isValid()) {
                map.fitBounds(bounds);
            }
        }
    }

    load_features();

    function render_spatial_resource() {
        $.ajax(fetch_spatial_resources).done(function (data) {
            if (data.length === 0) return;
            var spatialResources = {};
            $.each(data, function (idx, resource) {
                var name = resource.name;
                var layers = {};
                var group = new L.LayerGroup();
                $.each(resource.spatial_resources, function (i, spatial_resource) {
                    var layer = L.geoJson(spatial_resource.geom).addTo(group);
                    layers.name = spatial_resource.name;
                    layers.group = group;
                });
                spatialResources[name] = layers;
            });
            $.each(spatialResources, function (sr) {
                var layer = spatialResources[sr];
                layerscontrol.addOverlay(layer.group, layer.name, sr);
            });
        });
    }

    render_spatial_resource();

    function geoLocate() {
        return function (event) {
            map.locate({ setView: true });
        };
    }

    function add_map_controls() {
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

            onAdd: function () {
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

        function add_popup_actions() {
            map.on('popupopen', function () {
                $('#spatial-pop-up').on('click', function () {
                    map.closePopup();
                });
            });
        }

        add_popup_actions();

        return map;
    }

    add_map_controls();

};

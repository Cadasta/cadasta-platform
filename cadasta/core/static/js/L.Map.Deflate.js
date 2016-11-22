L.Deflate = function(options) {
    var removedPaths = [];
    var minSize = options.minSize || 10;
    var layer, map;
    var zoomBins = {};
    var startZoom;
    var markers = L.markerClusterGroup();

    function isCollapsed(path, zoom) {
        var bounds = path.getBounds();

        var ne_px = map.project(bounds.getNorthEast(), zoom);
        var sw_px = map.project(bounds.getSouthWest(), zoom);

        var width = ne_px.x - sw_px.x;
        var height = sw_px.y - ne_px.y;
        return (height < minSize || width < minSize);
    }

    function getZoomThreshold(path) {
        var zoomThreshold = null;
        var zoom = map.getZoom();
        if (isCollapsed(path, map.getZoom())) {
            while (!zoomThreshold) {
                zoom += 1;
                if (!isCollapsed(path, zoom)) {
                    zoomThreshold = zoom - 1;
                }
            }
        } else {
            while (!zoomThreshold) {
                zoom -= 1;
                if (isCollapsed(path, zoom)) {
                    zoomThreshold = zoom;
                }
            }
        }
        return zoomThreshold;
    }

    function layeradd(event) {
        var feature = event.layer;
        if (feature instanceof L.Marker && layer !== markers) {
            layer.removeLayer(feature);
            markers.addLayer(feature);
        } else if (!feature._layers && feature.getBounds && !feature.zoomThreshold && !feature.marker) {
            var zoomThreshold = getZoomThreshold(feature);
            var marker = L.marker(feature.getBounds().getCenter());

            if (feature._popupHandlersAdded) {
                marker.bindPopup(feature._popup._content)
            }

            var events = feature._events;
            for (var event in events) {
                if (events.hasOwnProperty(event)) {
                    var listeners = events[event];
                    for (var i = 0, len = listeners.length; i < len; i++) {
                        marker.on(event, listeners[i].fn) 
                    }
                }
            }

            feature.zoomThreshold = zoomThreshold;
            feature.marker = marker;
            feature.zoomState = map.getZoom();
            
            layer.removeLayer(feature);
            if (map.getZoom() <= zoomThreshold) {
                markers.addLayer(feature.marker);
            } else {
                markers.addLayer(feature);
            }

            if (zoomBins[zoomThreshold]) {
                zoomBins[zoomThreshold].push(feature);
            } else {
                zoomBins[zoomThreshold] = [feature];
            }
        }
    }

    function zoomstart() {
        startZoom = map.getZoom();
    }

    function deflate() {
        var bounds = map.getBounds();
        var endZoom = map.getZoom();
        var show = startZoom < endZoom;
        var markersToAdd = []
        var markersToRemove = [];

        var start = (show ? startZoom : endZoom);
        var end = (show ? endZoom : startZoom);

        for (var i = start; i <= end; i++) {
            if (zoomBins[i]) {
                var features = zoomBins[i];

                for (var j = 0, len = features.length; j < len; j++) {
                    if (features[j].zoomState !== endZoom && features[j].getBounds().intersects(bounds)) {
                        if (show) {
                            layer.addLayer(features[j]);
                            markersToRemove.push(features[j].marker);
                        } else {
                            layer.removeLayer(features[j]);
                            markersToAdd.push(features[j].marker);
                        }
                        features[j].zoomState = endZoom;
                    }
                }
            }
        }
        markers.removeLayers(markersToRemove);
        markers.addLayers(markersToAdd);
    }

    function addTo(addToMap) {
        layer = options.layerGroup || addToMap;
        map = addToMap;

        markers.addTo(map);
        layer.on('layeradd', layeradd);
        map.on('zoomstart', zoomstart);
        map.on('zoomend', deflate);
        map.on('dragend', deflate);
    }

    return { addTo: addTo }
}

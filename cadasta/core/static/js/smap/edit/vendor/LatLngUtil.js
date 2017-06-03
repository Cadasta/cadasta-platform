/**
 * @class L.LatLngUtil
 * @aka LatLngUtil
 */
var LatLngUtil = {
    // Clones a LatLngs[], returns [][]

    // @method cloneLatLngs(LatLngs[]): L.LatLngs[]
    // Clone the latLng point or points or nested points and return an array with those points
    cloneLatLngs: function (latlngs) {
        var clone = [];
        for (var i = 0, l = latlngs.length; i < l; i++) {
            // Check for nested array (Polyline/Polygon)
            if (Array.isArray(latlngs[i])) {
                clone.push(LatLngUtil.cloneLatLngs(latlngs[i]));
            } else {
                clone.push(this.cloneLatLng(latlngs[i]));
            }
        }
        return clone;
    },

    // @method cloneLatLng(LatLng): L.LatLng
    // Clone the latLng and return a new LatLng object.
    cloneLatLng: function (latlng) {
        return L.latLng(latlng.lat, latlng.lng);
    },

    copyLayer: function (layer) {
        if (layer instanceof L.Rectangle) {
            var rect = L.rectangle(layer.getLatLngs(), { draggable: true });
            rect.feature = layer.feature;
            return rect;
        }
        if (layer instanceof L.Polygon) {
            var poly = L.polygon(layer.getLatLngs(), { draggable: true });
            poly.feature = layer.feature;
            return poly;
        }
        if (layer instanceof L.Marker) {
            var marker = L.marker(layer.getLatLng(), { draggable: true });
            marker.feature = layer.feature;
            return marker;

        } else {
            var line = L.polyline(layer.getLatLngs(), { draggable: true });
            line.feature = layer.feature;
            return line;
        }
    },
};

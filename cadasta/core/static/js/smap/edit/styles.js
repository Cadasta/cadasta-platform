Styles = {

    setSelectedStyle: function (layer) {
        if (layer instanceof L.Polygon || layer instanceof L.Rectangle) {
            layer.setStyle({
                fillColor: '#f06eaa',
                color: '#f06eaa',
                weight: 5,
                fillOpacity: 0.2,
                fill: true,
                opacity: 0.5,
                dashArray: null,
                clickable: true
            });
        }
        if (layer instanceof L.Polyline) {
            layer.setStyle({
                color: '#f06eaa',
                weight: 4,
                opacity: 0.5,
                dashArray: null
            });
        }
    },

    setEditStyle: function (layer) {
        if (layer instanceof L.Polygon || layer instanceof L.Rectangle) {
            layer.setStyle({
                fillColor: '#f06eaa',
                dashArray: '10, 10',
                color: '#fe57a1',
                weight: 5,
                opacity: 0.6,
                fillOpacity: 0.1,
                clickable: true
            });
        }
        if (layer instanceof L.Polyline) {
            layer.setStyle({
                dashArray: '10, 10',
                color: '#fe57a1',
                weight: 5,
                opacity: 0.6,
            });
        }
    },

    setDeleteStyle: function (layer) {
        if (layer instanceof L.Polygon || layer instanceof L.Rectangle) {
            layer.setStyle({
                fillColor: 'red',
                color: 'red',
                dashArray: '10, 10'
            });
        }
        if (layer instanceof L.Polyline) {
            layer.setStyle({
                color: 'red',
                dashArray: '10, 10'
            });
        }
    },

    resetStyle: function (layer) {
        if (layer instanceof L.Polygon || layer instanceof L.Rectangle) {
            layer.setStyle({
                weight: 2,
                color: 'blue',
                fillColor: 'blue',
                stroke: true,
                fill: true,
                fillOpacity: 0.2,
                opacity: 1,
                dashArray: null,
            });
        }
        if (layer instanceof L.Polyline) {
            layer.setStyle({
                weight: 2,
                color: 'blue',
                stroke: true,
                opacity: 1,
                dashArray: null,
            });
        }
    }
}

Styles = {

    setSelectedStyle: function (layer) {
        if (layer instanceof L.Polygon || layer instanceof L.Rectangle) {
            layer.setStyle({
                fillColor: '#f06eaa',
                color: '#f06eaa',
                weight: 4,
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
                weight: 4,
                opacity: 0.5,
                fillOpacity: 0.2,
                clickable: true
            });
        }
        if (layer instanceof L.Polyline) {
            layer.setStyle({
                dashArray: '10, 10',
                color: '#fe57a1',
                weight: 4,
                opacity: 0.5,
            });
        }
    },

    setDeleteStyle: function (layer) {
        if (layer instanceof L.Polygon || layer instanceof L.Rectangle) {
            layer.setStyle({
                fillColor: 'red',
                color: 'red',
                dashArray: '10, 10'
            })
        }
        if (layer instanceof L.Polyline) {
            layer.setStyle({
                color: 'red',
                dashArray: '10, 10'
            })
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
                strokeWidth: 3,
                fillOpacity: 0.3,
                opacity: .5
            });
        }
        if (layer instanceof L.Polyline) {
            layer.setStyle({
                weight: 2,
                color: 'blue',
                stroke: true,
                strokeWidth: 3
            });
        }
    }
}

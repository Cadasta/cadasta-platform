Tooltip = L.Class.extend({

    EDIT_ENABLED: 'Click cancel to undo changes. <br/>' +
        'Drag handles, or marker to edit feature. <br/>' +
        'Click on a handle to delete it.',

    START_DELETE: 'Click on the highlighted feature to remove it.',
    CONTINUE_DELETE: 'Click cancel to undo or save to save deletion.',
    DELETE_LAYER: 'Click cancel to undo or save to save deletion.',

    VERTEX_DRAG: 'Release mouse to finish drawing.',

    FINISH_LINE: 'Click on last point to finish line.',
    CONTINUE_LINE: 'Click to continue line',

    CONTINUE_POLYGON: 'Click to continue adding vertices.',
    FINISH_POLYGON: 'Click to continue adding vertices.<br/>' +
        'Click last point to finish polygon.',

    ADD_MARKER: 'Click on the map to add a marker.',
    ADD_RECTANGLE: 'Click and drag on the map to create a rectangle.',
    ADD_POLYGON: 'Click on the map to start a new polygon.',
    ADD_LINESTRING: 'Click on the map to start a new line.',

    UPDATE_MULTIPOLYGON: 'Click on the map update the multipolygon.',
    UPDATE_MULTILINESTRING: 'Click on the map to update the multilinestring.',


    _enabled: false,


    initialize: function (map) {
        this._map = map;
        this._popupPane = map._panes.popupPane;
        this._container = L.DomUtil.create(
            'div', 'editor-tooltip', this._popupPane);

        this._map.on('mouseout', this._onMouseOut, this);
    },

    update: function (labelText) {
        if (!this._enabled) this._enable();
        if (!this._container) {
            return this;
        }
        this._container.innerHTML = labelText;
        return this;
    },

    remove: function () {
        if (this._enabled) this._disable();
    },

    _enable: function () {
        L.DomEvent.on(this._map, 'mousemove', this._move, this);
        this._enabled = true;
    },

    _disable: function () {
        this._container.innerHTML = '';
        this._container.style.visibility = 'hidden';
        L.DomEvent.off(this._map, 'mousemove', this._move, this);
        this._enabled = false;
    },

    _move: function (e) {
        if (this._container.style.visibility === 'hidden') {
            this._container.style.visibility = 'visible';
        }
        this._container.style.left = e.layerPoint.x + 'px';
        this._container.style.top = e.layerPoint.y + 'px';
    },

    _onMouseOut: function () {
        if (this._container) {
            this._container.style.visibility = 'hidden';
        }
    }

});

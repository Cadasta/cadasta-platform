/* eslint-env jquery */


var Location = L.Editable.extend({

    _deleting: false,
    _deleted: false,
    _canceled: false,
    _new: false,
    _dirty: false,

    layer: null,
    feature: null,

    initialize: function (map, options) {
        this._undoBuffer = {};
        this._original_state = [];
        this.on('editable:drawing:start', this._drawStart, this);
        this.on('editable:drawing:end', this._drawEnd, this);
        this.on('editable:drawing:cancel', this._drawCancel, this);
        L.Editable.prototype.initialize.call(this, map, options);
    },

    /**************
    EDIT FUNCTIONS
    **************/

    // Triggered when the 'edit tool' button is clicked'
    _startEdit: function () {
        if (this.layer) {
            this._backupLayer( initial_edit = true);
            this.layer.enableEdit(this.map);
            this.layer._dirty = true;
        }
    },

    // triggered when starting edit process, and on final "save/cancel" buttons
    _stopEdit: function () {
        if (this.layer) {
            this.layer.disableEdit(this.map);
            this._clearBackup();
            this.layer._dirty = false;
            this._deleted = false;
        }
    },

    // Update the geometry, and the geometry form field.
    _saveEdit: function (final) {
        this.layer.disableEdit();
        var geom = this.layer.toGeoJSON().geometry;
        this.layer.feature.geometry = geom;
        if (!this.layer._new) {
            this._backupLayer();
        }
        var gj = JSON.stringify(geom);
        $('textarea[name="geometry"]').html(gj);
        if (final) {
            this.layer._new = false;
            this._clearBackup(final);
        }
    },

    // revert latest editing change.
    _undoEdit: function (final) {
        this._undo(final);
        this._deleting = this._deleted = false;

        if (final) {
            this._clearBackup(final);
        }
    },

    // either revert to the most recent state, or back to the original_state.
    _undo: function (final) {
        var latLngs;

        if (this.layer) {
            this.layer.disableEdit();

            if (final) {
                if (this.layer._new || !this._original_state[0]) {
                    this._setDeleted();
                    this._saveDelete();
                    return;

                } else if (this._original_state[0]) {
                    latLngs = this._original_state[0];
                }
            } else {
                var latLngs_dict = this._undoBuffer;
                latLngs = latLngs_dict[this.layer._leaflet_id];
            }

            if (latLngs && latLngs.latlngs) {
                if (latLngs.layer instanceof L.Marker) {
                    latLngs.layer.setLatLng(latLngs.latlngs);
                } else {
                    latLngs.layer.setLatLngs(latLngs.latlngs);
                }

                this._drawEnd(latLngs.layer);
                this.featuresLayer.clearLayers();
            }

        }
    },

    /****************
    DELETE FUNCTIONS
    *****************/

    // initiate "deleting"
    _startDelete: function () {
        this._backupLayer();
        this._deleting = true;
        this._deleted = false;
    },

    // enable edit and remove the geometry.
    // if the layer is new, delete the entire layer? Is this right?
    _setDeleted: function (e) {
        this._backupLayer();
        if (this.layer instanceof L.Polyline || this.layer instanceof L.Polygon || this.layer instanceof L.Rectangle) {
            this.layer.enableEdit();
            this.layer.editor.deleteShape(this.layer._latlngs);
            this.layer.disableEdit();
        } else if (this.layer instanceof L.Marker) {
            this.layer.enableEdit();
            this.layer.remove();
        }
        this._deleted = true;
        this.featuresLayer.clearLayers();
    },

    // revert delete changes.
    _undoDelete: function (final) {
        this._undo(final);
        this._deleted = false;
        this._deleting = false;
    },

    // update geometry form field, set deleting to false, clear backup.
    _saveDelete: function () {
        if (this._deleted) {

            if (this.layer._new || !this._original_state[0]) {
                this.map.geojsonLayer.removeLayer(this.layer);
                this.layer = null;
            }
            $('textarea[name="geometry"]').html('');
        }
        this._deleting = false;
        this._clearBackup();
    },

    /**************
    DRAW FUNCTIONS
    **************/

    // fired when a geometry button is clicked.
    _drawStart: function (e) {},

    // fired when adding a new geometry, or replacing an old geometry
    _drawEnd: function (e) {
        if (!this._hasDrawnFeature()) return;
        if (!this._checkValid(e.layer)) return;
        if (this._canceled) {
            this._canceled = false;
            if (this.layer) {
                e.layer = this.layer;
            } else {
                e.layer.remove();
                return;
            }
        }
        if (this.layer) {
            this._update(e.layer);
        } else {
            this._createNew(e.layer);
        }
        this.featuresLayer.clearLayers();
        this.layer.disableEdit();
        this.layer.dragging.disable();
        this._deleted = false;
        this._deleting = false;
    },

    _drawCancel: function (e) {
        this._canceled = true;
    },

    // fired when a geometry is deleted and a new one replaces the old one.
    _update: function (lyr) {
        this.layer.disableEdit();
        var geometry = lyr.toGeoJSON().geometry;
        var layer = LatLngUtil.copyLayer(lyr);
        L.stamp(layer);
        this.layer.feature.geometry = geometry;
        layer.feature = this.layer.feature;
        layer._new = this.layer._new;
        this.layer = layer;
        this._backupLayer();
        this._replaceGeoJSONFeature(this.layer);
        this.layer._dirty = true;
    },

    // only fired when 'adding location'
    _createNew: function (lyr) {
        var feature = lyr.toGeoJSON();
        var layer = LatLngUtil.copyLayer(lyr);
        feature.id = L.stamp(layer);
        layer.feature = feature;

        this.layer = layer;
        this.map.geojsonLayer.addLayer(this.layer);
        this.layer._new = true;
        this.layer._dirty = true;
    },

    _checkValid: function (layer) {
        if (layer instanceof L.Polygon || layer instanceof L.Rectangle || layer instanceof L.Polyline) {
            // check if a feature has been drawn
            if (!layer.getBounds().isValid()) return false;
            var bounds = layer.getBounds();
            var nw = bounds.getNorthWest();
            var se = bounds.getSouthEast();
            if (nw.lat === se.lat && nw.lng === se.lng) {
                this.featuresLayer.removeLayer(layer);
                return false;
            }
            return true;
        } else {
            return true;
        }
    },

    /*********
    UTILS
    ********/

    // if a geometry has been updated, it removes the old layer and replaces it with the new.
    _replaceGeoJSONFeature: function (layer) {
        this.map.geojsonLayer.eachLayer(function (l) {
            if (l.feature.id === layer.feature.id) {
                l.remove();
                this.map.geojsonLayer.removeLayer(l);
                this.map.geojsonLayer.addLayer(layer);
            }
        }, this);
    },

    // finds the feature id that matches the id in the url.
    _findLayer: function (fid) {
        var layer = null;
        this.map.geojsonLayer.eachLayer(function (l) {
            if (l.feature.id === fid) {
                layer = l;
                return;
            }
        });
        return layer;
    },

    // Stores the ORIGINAL version fo the geometry, and the version right before the lastest change.
    _backupLayer: function (initial_edit) {
        var cloneLatLngs;
        var originalLatLngs;

        this._undoBuffer = {};

        if (this.layer instanceof L.Marker) { 
            cloneLatLngs = LatLngUtil.cloneLatLng(this.layer.getLatLng());
        } else { 
            cloneLatLngs = LatLngUtil.cloneLatLngs(this.layer.getLatLngs());
        }

        this._undoBuffer[this.layer._leaflet_id] = {
            latlngs: cloneLatLngs,
            layer: this.layer,
        };
        // if the object is NEW, original state should always be empty
        // else, if it's the initial edit, it should save the very first shape.
        if (initial_edit && !this.layer._new && !this._original_state[0]) {
            // cannot use cloneLatLngs because it's not constant.
            if (this.layer instanceof L.Marker) { 
                originalLatLngs = LatLngUtil.cloneLatLng(this.layer.getLatLng());
            } else { 
                originalLatLngs = LatLngUtil.cloneLatLngs(this.layer.getLatLngs());
            }

            this._original_state.push({
                latlngs: originalLatLngs,
                layer: this.layer
            });
        }
    },

    // checks if the user has drawn a shape.
    // triggered after a geometry has bee completed.
    _hasDrawnFeature: function () {
        return this.featuresLayer.getLayers().length > 0;
    },

    // removes all information in the buffer.
    // if "final" removes the _original_state
    _clearBackup: function (final) {
        this._undoBuffer = {};
        if (final) {
            this._original_state = [];
        }
    },

    // fired when editing starts, and when final "cancel" is clicked.
    _reset: function () {
        this.layer = null;
        this.feature = null;
        this.featuresLayer.clearLayers();
        this._clearBackup(true);
    },

});


var LocationEditor = L.Evented.extend({

    _editing: false,
    _multi: false,
    _prevent_click: false,

    initialize: function (map, options) {
        this.map = map;
        map.locationEditor = this;
        this.location = new Location(map);
        map.editTools = this.location;
        this.toolbars = new EditorToolbars();

        this.tooltip = new Tooltip(map);

        this._addDeleteEvent();
        this._addRouterEvents();
        this._addEditableEvents();
    },

    // determines whether or not clicking on a location is "allowed"
    onLayerClick: function (e) {
        if (this.dirty() && !this.deleting()) return;
        var feature = e.target.feature;
        var layer = e.layer || e.target;
        if (this.preventClick() && this.location.layer && feature.id !== this.location.layer.feature.id) return;
        if (this.editing() && feature.id !== this.location.layer.feature.id) return;
        if (this.deleting()) {
            this.deleteLayer(layer, e);
            return;
        }
        if (!this.editing()) {
            window.location.href = "#/" + feature.properties.url + '/';
        }
        this.setEditable(feature, layer);
    },

    /********
    EDIT FUNCTIONS
    *********/

    // Make the currently selected location editable.
    setEditable: function (feature, layer) {
        if (this.location.layer) {
            if (this.location.layer.feature.id === feature.id) {
                return;
            } else {
                Styles.resetStyle(this.location.layer);
            }
        }

        layer.feature = feature;
        this.location.layer = layer;
        this.location.feature = feature;
        Styles.setSelectedStyle(layer);
    },

    // Triggered when finishing adding a geometry, clicking "edit tool" button
    edit: function () {
        this.tooltip.update(this.tooltip.EDIT_ENABLED);
        if (this.editing()) {
            return;
        }
        this.location._startEdit();
    },

    // Triggered by cancel in the map
    // Also manually triggered by "dispose"
    cancelEdit: function (final) {
        this.tooltip.remove();
        this._multi = false;
        this.location._undoEdit(final);
    },

    // checks if currently "editing";
    editing: function () {
        return this._editing;
    },

    // checks if prevent_click is true
    preventClick: function () {
        return this._prevent_click;
    },

    // checks if a location is "dirty".
    // Should be dirty until final "save/cancel"
    dirty: function () {
        if (this.location.layer) {
            return this.location.layer._dirty;
        }
    },

    // Triggered by click on geom button, cancel geom button, and "edit tool" button.
    // why is it being triggered by cancel?
    _editStart: function (e) {
        this._editing = true;
        this._prevent_click = true;
        Styles.setEditStyle(e.layer);
    },

    // Triggered when a geom is added, canceled, AND saved.
    _editStop: function (e) {
        this._editing = false;
        Styles.setSelectedStyle(e.layer);
    },

    /***************
    DELETE FUNCTIONS
    ***************/

    // finalizes "delete" on the map, not in form.
    delete: function () {
        this.tooltip.remove();
        this.location._saveDelete();
        if (this.deleted()) {
            this._disableEditToolbar();
        } else {
            Styles.setSelectedStyle(this.location.layer);
        }
    },

    // adds locations that had been deleted back.
    cancelDelete: function (final) {
        this.tooltip.remove();
        this.location._undoDelete(final);
        Styles.setSelectedStyle(this.location.layer);
    },

    // enables the delete button, starts delete process, and sets the style of the location to "deleting"
    startDelete: function () {
        this.tooltip.update(this.tooltip.START_DELETE);
        if (this.location.layer) {
            this.location._startDelete();
            Styles.setDeleteStyle(this.location.layer);
        }
    },

    // checks to see if a location is in the process of being deleted.
    deleting: function () {
        return this.location._deleting;
    },

    // Checks to see if a location has been deleted.
    deleted: function () {
        return this.location._deleted;
    },

    // Only fired when clicking 'delete geometry' in map.
    deleteLayer: function (layer, e) {
        this.tooltip.update(this.tooltip.CONTINUE_DELETE);
        var currentLayer = this.location.layer;
        if (currentLayer.feature.id !== layer.feature.id) {
            return;
        }
        this.location._setDeleted(e);
    },

    /************************
    DELETE LOCATION FUNCTIONS
    *************************/

    // ONLY fired when clicking "delete location" on location detail page.
    _removeLayer: function () {
        var hash_path = window.location.hash.slice(1) || '/';
        var fid = hash_path.split('/')[3];
        var layer = this.location._findLayer(fid);
        if (layer) layer.remove();
    },

    /********************* 
    NEW LOCATION FUCTIONS
    *********************/

    // triggered when "add location" is clicked.
    _addNew: function () {
        this._resetView();
        this._addEditControls();
        this._disableEditToolbar();
    },

    // checks if this is a newly added location.
    isNew: function () {
        if (this.location.layer) {
            return this.location.layer._new;
        }
    },

    /**************
    DRAW FUNCTIONS
    ***************/

    startRectangle: function () {
        this.tooltip.update(this.tooltip.ADD_RECTANGLE);
        this.location.startRectangle();
    },

    startPolygon: function () {
        this.tooltip.update(this.tooltip.ADD_POLYGON);
        this.location.startPolygon();
    },

    addMulti: function (e, type) {
        this._multi = true;
        if (type instanceof L.Editable.PolygonEditor) {
            this.tooltip.update(this.tooltip.UPDATE_MULTIPOLYGON);
        } else {
            this.tooltip.update(this.tooltip.UPDATE_MULTILINESTRING);
        }
        this.location.layer.editor.newShape();
    },

    startPolyline: function () {
        this.tooltip.update(this.tooltip.ADD_LINESTRING);
        this.location.startPolyline();
    },

    startMarker: function () {
        this.tooltip.update(this.tooltip.ADD_MARKER);
        this.location.startMarker();
    },

    // checked to see if edit tool button can be enabled.
    hasEditableLayer: function () {
        return ((this.location.layer !== null ? true : false) ||
                this.hasDrawnFeature()) &&
            (!this.deleting() && !this.deleted());
    },

    // checks to see if there is a layer that can be edited
    hasDrawnFeature: function () {
        return this.location.featuresLayer.getLayers().length > 0;
    },

    // Only fired when cancel-action button is clicked.
    cancelDrawing: function (e) {
        this.location.stopDrawing();
        this.tooltip.remove();
        this._editing = false;
        if (!this.location.layer) {
            this._disableEditToolbar();
        }
    },

    // Fired every time a geometry button is clicked.
    _drawStart: function (e) {},

    // fired every a geometry is 'completed', or the cancel-action button is clicked.
    // Adds a click event if there is a layer, and automatically enables the edit toolbar.
    _drawEnd: function (e) {
        this._cancelDraw();

        if (this.location.layer) {
            this.tooltip.remove();
            if (!this.location.layer._events.hasOwnProperty('click')) {
                this.location.layer.on('click', this.onLayerClick, this);
            }
            this._enableEditToolbar();

            if (!this._multi) {
                Styles.setSelectedStyle(this.location.layer);
                
                // This temporarily saves geometries once they're added to the map,
                // rather than having them go directly into "edit" mode.
                if (this.isNew()) {
                    this.save();
                }
            }

        }
    },

    _vertexNew: function (e) {
        var latlngs;
        if (e.layer.editor instanceof L.Editable.PolylineEditor) {
            latlngs = e.layer._latlngs;
            if (latlngs.length >= 1) {
                this.tooltip.update(this.tooltip.FINISH_LINE);
            } else {
                this.tooltip.update(this.tooltip.CONTINUE_LINE);
            }
        }
        if (e.layer.editor instanceof L.Editable.PolygonEditor) {
            latlngs = e.layer._latlngs[0];
            if (latlngs.length < 2) {
                this.tooltip.update(this.tooltip.CONTINUE_POLYGON);
            }
            if (latlngs.length >= 2 && e.layer.editor instanceof L.Editable.PolygonEditor) {
                this.tooltip.update(this.tooltip.FINISH_POLYGON);
            }
        }
    },

    _vertexDrag: function (e) {
        this.tooltip.update(this.tooltip.VERTEX_DRAG);
    },

    _vertexDragend: function (e) {
        this.tooltip.update(this.tooltip.EDIT_ENABLED);
    },

    /*******************
    SAVING vs. DISPOSING
    ********************/

    // fired when clicking "save" on the map, as well as the final "Save" in the form
    // if "final", the Save button in the form has been clicked
    save: function (final) {
        this.tooltip.remove();
        this._multi = false;
        if (this.deleting()) {
            this.location._saveDelete();
        } else if (this.editing() || this.dirty()) {
            this.location._saveEdit(final);
        }
    },

    // ONLY fired when the "big" cancel button in form is clicked.
    // This is only time it should rely on _original_state
    dispose: function () {
        if (this.deleting() || this.deleted()) {
            this.cancelDelete( final = true);
        }

        if (this.editing() || this.dirty()) {
            this.cancelEdit( final = true);
        }

        this._resetView();
    },

    /**********************************
    EDITOR TOOLBARS && DOM MANIPULATORS
    ***********************************/

    // When editing an existing location, there won't be layers if the page has been refreshed.
    _setUpEditor: function (e) {
        if (!this.location.layer) {
            var hash_path = window.location.hash.slice(1) || '/';
            var fid = hash_path.split('/')[3];
            if (this.map.geojsonLayer.getLayers().length > 0) {
                var layer = this.location._findLayer(fid);
                this.location.layer = layer;
                Styles.setSelectedStyle(this.location.layer);
                this.edit();
                this._addEditControls();
            }
        } else {
            this._addEditControls();
        }
    },

    // adds the leaflet edit toolbar.
    // automatically clicks on the edit button so that editing locations is automatic
    _addEditControls: function () {
        var map = this.map;
        this.toolbars.forEach(function (toolbar) {
            toolbar.addTo(map);
        });
        this._enableEditToolbar(active = true);
    },

    // removes the leaflet edit toolbars. Turns prevent click off.
    _removeEditControls: function () {
        var map = this.map;
        this.toolbars.forEach(function (toolbar) {
            if (toolbar) {
                map.removeControl(toolbar);
            }
        });
        this.location._stopEdit();
        this._prevent_click = false;
        this.tooltip.remove();
    },

    // activates edit/delete tool logo on map.
    // If 'active' === true, the "save/cancel" buttons appear automatically.
    _enableEditToolbar: function (active) {
        active = active || false;
        var editLink = $('a.edit-action').get(0);
        var deleteLink = $('a.delete-action').get(0);
        editLink.href = window.location.href;
        deleteLink.href = window.location.href;
        if (active) {
            editLink.click();
            Styles.setEditStyle(this.location.layer);
        }
        $('span#edit, span#delete').removeClass('smap-edit-disable');
    },

    // deactivates the edit tool logo on map
    _disableEditToolbar: function (deactivate) {
        deactivate = deactivate || false;
        var edit = $('ul.leaflet-smap-edit a').prop('disabled', 'disabled');
        $('span#edit, span#delete').addClass('smap-edit-disable');
        if (deactivate) {
            var editLink = $('a.edit-action').get(0);
            editLink.href = window.location.href;
            editLink.click();
        }
    },

    // Automatically clicks the edit/delete cancel buttons.
    // if reset, the location style goes back to default
    _cancelEdit: function (reset) {
        reset = reset || true;
        var cancelEdit = $('a.cancel-edit'),
            cancelDelete = $('a.cancel-delete');
        if (cancelEdit.is(':visible')) {
            cancelEdit.get(0).click();
        }
        if (cancelDelete.is(':visible')) {
            cancelDelete.get(0).click();
        }
        if (this.location.layer && reset) {
            Styles.resetStyle(this.location.layer);
        }
    },

    // triggered when cancel-action button is clicked.
    // closes cancel-action button
    _cancelDraw: function () {
        var cancelDraw = $('a.cancel-draw');
        cancelDraw.each(function (idx, ele) {
            if ($(ele).is(':visible')) {
                // ele.click();
                var ul = $(ele).closest('ul');
                $(ul).css('display', 'none');
            }
        });
    },

    // returns view back to normal
    _resetView: function () {
        this._editing = false;
        this._multi = false;
        this._prevent_click = false;
        this._removeEditControls();

        if (!window.location.hash.includes('/edit/')) {
            Styles.resetStyle(this.location.layer);
        }

        this.location._reset();
    },

    /***********
    EVENTS
    ************/

    _addDeleteEvent: function () {
        this.on('location:delete', this._removeLayer, this);
    },

    _addRouterEvents: function () {
        // router events
        this.on('route:location:edit', this._setUpEditor, this);
        this.on('route:location:new', this._addNew, this);
        this.on('route:location:detail', this._removeEditControls, this);
        this.on('route:overview', this._resetView, this);
        this.on('route:map', this._resetView, this);
    },

    _addEditableEvents: function () {
        // edit events
        this.location.on('editable:enable', this._editStart, this);
        this.location.on('editable:disable', this._editStop, this);
        this.location.on('editable:drawing:start', this._drawStart, this);
        this.location.on('editable:drawing:end', this._drawEnd, this);
        this.location.on('editable:vertex:drag', this._vertexDrag, this);
        this.location.on('editable:vertex:dragend', this._vertexDragend, this);
        this.location.on('editable:drawing:click', this._vertexNew, this);
    }

});

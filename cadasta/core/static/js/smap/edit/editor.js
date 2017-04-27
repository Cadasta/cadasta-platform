/* eslint-env jquery */


var Location = L.Editable.extend({

    _deleting: false,
    _deleted: false,
    _new: false,
    _dirty: false,
    _original_state: {},

    layer: null,
    feature: null,

    initialize: function (map, options) {
        this._undoBuffer = {};
        this.on('editable:drawing:start', this._drawStart, this);
        this.on('editable:drawing:end', this._drawEnd, this);
        L.Editable.prototype.initialize.call(this, map, options);
    },

    // edit functions

    _startEdit: function () {
        if (this.layer) {
            if (!this.layer._new) {
                this._backupLayer(true);
            }
            this.layer.enableEdit(this.map);
            this.layer._dirty = true;
        }
    },

    _stopEdit: function () {
        if (this.layer) {
            this.layer.disableEdit(this.map);
            this._clearBackup();
        }
    },

    _saveEdit: function () {
        this.layer.disableEdit();
        var geom = this.layer.toGeoJSON().geometry;
        this.layer.feature.geometry = geom;
        if (!this.layer._new) {
            this._backupLayer();
        }
        var gj = JSON.stringify(geom);
        $('textarea[name="geometry"]').html(gj);
        this.layer._dirty = false;
        this.layer._new = false;
    },

    _undoEdit: function (cancel_form) {
        this._undo(cancel_form);
        if (this.layer) this.layer._dirty = false;
        this._deleting = this._deleted = false;
    },

    _undo: function (cancel_form) {
        if (this.layer) {
            this.layer.disableEdit();
            var latLngs_dict = cancel_form ? this._original_state : this._undoBuffer;
            latLngs = latLngs_dict[this.layer._leaflet_id];

            if (latLngs && latLngs.latlngs) {
                if (this.layer instanceof L.Marker) {
                    this.layer.setLatLng(latLngs.latlngs);
                    this.map.geojsonLayer.removeLayer(this.layer);
                    this.map.geojsonLayer.addLayer(this.layer);
                } else {
                    this.layer.setLatLngs(latLngs.latlngs);
                    this.map.geojsonLayer.removeLayer(this.layer);
                    this.map.geojsonLayer.addLayer(this.layer);
                }
                this._clearBackup();
            } else if (this.layer._new !== undefined) {
                this._setDeleted();
            }

            if (cancel_form) {
                this._original_state = {};
            }
        }
    },

    // delete functions

    _startDelete: function () {
        this.layer.disableEdit();
        if (!this.layer._new) {
            this._backupLayer();
        }
        this._deleting = true;
        this._deleted = false;
    },

    _setDeleted: function (e) {
        if (!this.layer._new) {
            this._backupLayer();
        }
        if (this.layer instanceof L.Polyline || this.layer instanceof L.Polygon || this.layer instanceof L.Rectangle) {
            this.layer.enableEdit();
            this.layer.editor.deleteShape(this.layer._latlngs);
            this.layer.disableEdit();
            // this.map.geojsonLayer.removeLayer(this.layer);
            this._deleted = true;
        } else if (this.layer instanceof L.Marker) {
            this.layer.enableEdit();
            this.layer.remove();
            // this.map.geojsonLayer.removeLayer(this.layer);
            this._deleted = true;
        }

        this.map.geojsonLayer.removeLayer(this.layer);

        if (this.layer._new) {
            this.layer = null;
        }

        this.featuresLayer.clearLayers();
    },

    _undoDelete: function () {
        this._undo();
        this._deleted = false;
        this._deleting = false;
    },

    _saveDelete: function () {
        if (this._deleted) {
            $('textarea[name="geometry"]').html('');
            this.featuresLayer.clearLayers();
            this._clearBackup();
        }
        this._deleting = false;
    },

    // draw functions

    _drawStart: function (e) {},

    _drawEnd: function (e) {
        if (!this._hasDrawnFeature()) return;
        if (!this._checkValid(e.layer)) return;
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

    _update: function (lyr) {
        this.layer.disableEdit();
        var geometry = lyr.toGeoJSON().geometry;
        var layer = LatLngUtil.copyLayer(lyr);
        L.stamp(layer);
        this.layer.feature.geometry = geometry;
        layer.feature = this.layer.feature;
        this.layer = layer;
        if (!this.layer._new) {
            this._backupLayer();
        }
        this._replaceGeoJSONFeature(this.layer);
        this.layer._dirty = true;
    },

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

    // utils

    _replaceGeoJSONFeature: function (layer) {
        this.map.geojsonLayer.eachLayer(function (l) {
            if (l.feature.id === layer.feature.id) {
                l.remove();
                this.map.geojsonLayer.addLayer(layer);
            }
        }, this);
    },

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

    _backupLayer: function (initial_edit) {
        this._undoBuffer = {};
        if (this.layer instanceof L.Polyline || this.layer instanceof L.Polygon || this.layer instanceof L.Rectangle) {
            this._undoBuffer[this.layer._leaflet_id] = {
                latlngs: LatLngUtil.cloneLatLngs(this.layer.getLatLngs()),
            };

            if (initial_edit && Object.keys(this._original_state).length === 0) {
                this._original_state[this.layer._leaflet_id] = {
                    latlngs: LatLngUtil.cloneLatLngs(this.layer.getLatLngs()),
                };
            }
        }
        if (this.layer instanceof L.Marker) {
            this._undoBuffer[this.layer._leaflet_id] = {
                latlngs: LatLngUtil.cloneLatLng(this.layer.getLatLng()),
            };
            if (initial_edit && Object.keys(this._original_state).length === 0) {
                this._original_state[this.layer._leaflet_id] = {
                    latlngs: LatLngUtil.cloneLatLng(this.layer.getLatLngs()),
                };
            }
        }
    },

    _hasDrawnFeature: function () {
        return this.featuresLayer.getLayers().length > 0;
    },

    _clearBackup: function () {
        this._undoBuffer = {};
    },

    _reset: function () {
        this.layer = null;
        this.feature = null;
        this.featuresLayer.clearLayers();
        this._clearBackup();
    },

});


var LocationEditor = L.Evented.extend({

    _editing: false,
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

    onLayerClick: function (e) {
        if (this.dirty() && !this.deleting()) return;
        var feature = e.target.feature;
        var layer = e.layer || e.target;
        if (this.preventClick() && feature.id !== this.location.layer.feature.id) return;
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

    // edit functions

    setEditable: function (feature, layer) {
        if (this.location.layer) {
            Styles.resetStyle(this.location.layer);
        }
        layer.feature = feature;
        this.location.layer = layer;
        this.location.feature = feature;
        Styles.setSelectedStyle(layer);
    },

    edit: function () {
        this.tooltip.update(this.tooltip.EDIT_ENABLED);
        if (this.editing()) {
            return;
        }
        this.location._startEdit();
    },

    cancelEdit: function (cancel_form) {
        this.tooltip.remove();
        this.location._undoEdit(cancel_form);
    },

    editing: function () {
        return this._editing;
    },

    preventClick: function () {
        return this._prevent_click;
    },

    dirty: function () {
        if (this.location.layer) {
            return this.location.layer._dirty;
        }
    },

    _editStart: function (e) {
        this._editing = true;
        this._prevent_click = true;
        Styles.setEditStyle(e.layer);
    },

    _editStop: function (e) {
        this._editing = false;
        Styles.setSelectedStyle(e.layer);
    },

    // delete functions

    delete: function () {
        this.tooltip.remove();
        this.location._saveDelete();
        if (this.location._deleted) {
            this._disableEditToolbar();
        } else {
            Styles.setSelectedStyle(this.location.layer);
        }
    },

    cancelDelete: function () {
        this.tooltip.remove();
        this.location._undoDelete();
        Styles.setSelectedStyle(this.location.layer);
    },

    startDelete: function () {
        this.tooltip.update(this.tooltip.START_DELETE);
        if (this.location.layer) {
            this.location._startDelete();
            Styles.setDeleteStyle(this.location.layer);
        }
    },

    deleting: function () {
        return this.location._deleting;
    },

    deleted: function () {
        return this.location._deleted;
    },

    deleteLayer: function (layer, e) {
        this.tooltip.update(this.tooltip.CONTINUE_DELETE);
        var currentLayer = this.location.layer;
        if (currentLayer.feature.id !== layer.feature.id) {
            return;
        }
        this.location._setDeleted(e);
    },

    _removeLayer: function () {
        var hash_path = window.location.hash.slice(1) || '/';
        var fid = hash_path.split('/')[3];
        var layer = this.location._findLayer(fid);
        if (layer) layer.remove();
    },

    // new location functions

    _addNew: function () {
        this._resetView();
        this._addEditControls();
        this._disableEditToolbar();
    },

    isNew: function () {
        if (this.location.layer) {
            return this.location.layer._new;
        }
    },

    // draw functions

    startRectangle: function () {
        this.tooltip.update(this.tooltip.ADD_RECTANGLE);
        this.location.startRectangle();
    },

    startPolygon: function () {
        this.tooltip.update(this.tooltip.ADD_POLYGON);
        this.location.startPolygon();
    },

    addMulti: function (e, type) {
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

    hasEditableLayer: function () {
        return ((this.location.layer !== null ? true : false) ||
                this.hasDrawnFeature()) &&
            (!this.deleting() && !this.deleted());
    },

    hasDrawnFeature: function () {
        return this.location.featuresLayer.getLayers().length > 0;
    },

    cancelDrawing: function (e) {
        this.location.stopDrawing();
        this.tooltip.remove();
        if (this.location.layer) {
            this.deleteLayer(this.location.layer, e);
            this.delete();
        }
        this._disableEditToolbar(deactivate = true);
    },

    dispose: function () {
        this.cancelEdit(false);
        this._resetView();
    },

    _drawStart: function (e) {
        // this._addTooltip();
    },

    _drawEnd: function (e) {
        this._cancelDraw();
        if (this.location.layer) {
            this.tooltip.remove();
            if (!this.location.layer._events.hasOwnProperty('click')) {
                this.location.layer.on('click', this.onLayerClick, this);
            }
            this._enableEditToolbar(active = true);
            Styles.setEditStyle(this.location.layer);
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

    // saving

    save: function () {
        this.tooltip.remove();
        this.location._saveEdit();
        this._editing = false;
    },

    // editor toolbars

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
            } else {
                this.map.on('endtileload', function () {
                    var layer = this.location._findLayer(fid);
                    this.location.layer = layer;
                    Styles.setSelectedStyle(this.location.layer);
                    this.edit();
                    this._addEditControls();
                }, this);
            }
        } else {
            this._addEditControls();
        }
    },

    _addEditControls: function () {
        var map = this.map;
        this.toolbars.forEach(function (toolbar) {
            toolbar.addTo(map);
        });
        this._enableEditToolbar(active = true);
    },

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

    _resetView: function () {
        this._editing = false;
        this._prevent_click = false;
        this._removeEditControls();
        Styles.resetStyle(this.location.layer);
        this.location._reset();
    },

    _cleanForm: function () {
        // if an add location form is canceled, geometry should be removed
        this.cancelEdit(true);
        this.location._saveDelete();
    },

    // events

    _addDeleteEvent: function () {
        this.on('location:delete', this._removeLayer, this);
        this.on('location:reset', this._cleanForm, this);
        this.on('location:reset_dirty', this._cleanForm, this);
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

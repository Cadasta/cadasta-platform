var EditorToolbars = function () {

    var SubToolbar = L.Toolbar.extend({});

    var BaseToolbarAction = L.ToolbarAction.extend({
        initialize: function (map, options) {
            this.map = map;
            this.editor = map.locationEditor;
            this.tooltip = map.locationEditor.tooltip;
            L.setOptions(this, options);
            L.ToolbarAction.prototype.initialize.call(this, options);
        }
    });

    var SubAction = L.ToolbarAction.extend({
        initialize: function (map, action, options) {
            this.map = map;
            this.editor = map.locationEditor;
            this.action = action;
            L.setOptions(this, options);
            L.ToolbarAction.prototype.initialize.call(this, options);
        },
        addHooks: function () {
            this.action.disable();
        }
    });

    var CancelAction = SubAction.extend({
        options: {
            toolbarIcon: {
                html: 'Cancel',
                className: 'cancel-draw',
                tooltip: 'Cancel drawing'
            },
        },
        addHooks: function () {
            this.editor.cancelDrawing();
            SubAction.prototype.addHooks.call(this);
        }
    });

    // draw toolbars

    var DrawControl = BaseToolbarAction.extend({
        enable: function () {
            if (this.editor.deleting()) return;
            BaseToolbarAction.prototype.enable.call(this);
        }
    });

    var PolygonControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                html: '<span class="">▰</span>',
                tooltip: 'Draw a polygon',
            },
            subToolbar: new SubToolbar({
                className: 'cancel-draw-poly leaflet-subtoolbar',
                actions: [CancelAction],
            })
        },
        addHooks: function () {
            this.tooltip.innerHTML = 'Click on the map to start a polygon.';
            this.editor.startPolygon();
        }
    });

    var MultiGeomControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                html: '<span class="">▰▰</span>',
                className: 'add-multi',
                tooltip: 'Add a Multipolygon or Multilinestring',
            },
            subToolbar: new SubToolbar({
                className: 'cancel-add-multi leaflet-subtoolbar',
                actions: [CancelAction],
            })
        },
        addHooks: function () {
            this.tooltip.innerHTML = 'Click on the map to add a multipolygon or multilinestring.';
            this.editor.startMulti();
        },
        enable: function () {
            if (this.editor.location.layer.editEnabled() &&
                this.editor.hasEditableLayer() &&
                (this.editor.location.layer.editor instanceof L.Editable.PolygonEditor ||
                    this.editor.location.layer.editor instanceof L.Editable.PolylineEditor)) {
                DrawControl.prototype.enable.call(this);
            }
        }
    })
    var MarkerControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                html: '<span class="glyphicon glyphicon-map-marker"></span>',
                tooltip: 'Draw marker',
            },
            subToolbar: new SubToolbar({
                className: 'cancel-draw-marker leaflet-subtoolbar',
                actions: [CancelAction],
            })
        },
        addHooks: function () {
            this.tooltip.innerHTML = 'Click on the map to add a marker.';
            this.editor.startMarker();
        }
    });

    var LineControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                html: '<span>\/</span>',
                tooltip: 'Draw line',
            },
            subToolbar: new SubToolbar({
                className: 'cancel-draw-line leaflet-subtoolbar',
                actions: [CancelAction],
            })
        },
        addHooks: function () {
            this.tooltip.innerHTML = 'Click on the map to start a line.';
            this.editor.startPolyline();
        }
    });

    var RectangleControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                html: '<span>⬛</span>',
                tooltip: 'Draw a rectangle',
            },
            subToolbar: new SubToolbar({
                className: 'cancel-draw-rect leaflet-subtoolbar',
                actions: [CancelAction],
            })
        },
        addHooks: function () {
            this.tooltip.innerHTML = 'Click and drag on the map to create a rectangle.';
            this.editor.startRectangle();
        }
    });

    // edit tools

    var SaveEdit = SubAction.extend({
        options: {
            toolbarIcon: {
                html: 'Save',
                tooltip: 'Save edits'
            }
        },
        addHooks: function () {
            this.editor.save();
            SubAction.prototype.addHooks.call(this);
        }
    });

    var CancelEdit = SubAction.extend({
        options: {
            toolbarIcon: {
                html: 'Cancel',
                className: 'cancel-edit',
                tooltip: 'Cancel edits'
            },
        },
        addHooks: function () {
            this.editor.cancelEdit();
            SubAction.prototype.addHooks.call(this);
        }
    });

    var SaveDelete = SubAction.extend({
        options: {
            toolbarIcon: {
                html: 'Save',
                className: 'save-delete',
                tooltip: 'Save changes'
            },
        },
        addHooks: function () {
            this.editor.delete();
            SubAction.prototype.addHooks.call(this);
        }
    });

    var CancelDelete = SubAction.extend({
        options: {
            toolbarIcon: {
                html: 'Cancel',
                className: 'cancel-delete',
                tooltip: 'Cancel deletion'
            },
        },
        addHooks: function () {
            this.editor.cancelDelete();
            SubAction.prototype.addHooks.call(this);
        }
    });

    // main edit actions

    var EditAction = BaseToolbarAction.extend({
        options: {
            toolbarIcon: {
                html: '<span id="edit" class="glyphicon glyphicon-edit"></span> ',
                className: 'edit-action',
                tooltip: 'Edit feature',
            },
            subToolbar: new SubToolbar({
                className: 'leaflet-subtoolbar',
                actions: [SaveEdit, CancelEdit],
            })
        },
        addHooks: function () {
            this.editor.edit();
        },
        enable: function () {
            if (this.editor.hasEditableLayer()) {
                this.tooltip.innerHTML = 'Click cancel to undo changes. <br/>' +
                    'Drag handles, or marker to edit feature. <br/>' +
                    'Click on a handle to delete it.'
                L.ToolbarAction.prototype.enable.call(this);
            }
        }
    });

    var DeleteAction = BaseToolbarAction.extend({
        options: {
            toolbarIcon: {
                html: '<span id="delete" class="glyphicon glyphicon-trash"></span>',
                className: 'delete-action',
                tooltip: 'Delete feature',
            },
            subToolbar: new SubToolbar({
                className: 'leaflet-subtoolbar',
                actions: [SaveDelete, CancelDelete],
            })
        },
        addHooks: function () {
            this.tooltip.innerHTML = 'Click on a feature to remove.';
            this.editor.startDelete();
        },
        enable: function () {
            if (this.editor.hasEditableLayer()) {
                L.ToolbarAction.prototype.enable.call(this);
            }
        },
        disable: function () {
            if (this.editor.location._deleting && this.editor.location._deleted) return;
            L.ToolbarAction.prototype.disable.call(this);
        }
    });


    // toolbars
    var Toolbars = [];
    var EditToolbar = L.Toolbar.Control.extend({});
    var DrawToolbar = L.Toolbar.Control.extend({});

    Toolbars.push(new DrawToolbar({
        position: 'topleft',
        className: 'leaflet-smap-draw',
        actions: [
            LineControl, PolygonControl, MultiGeomControl,
            RectangleControl, MarkerControl
        ]
    }));

    Toolbars.push(new EditToolbar({
        position: 'topleft',
        className: 'leaflet-smap-edit',
        actions: [EditAction, DeleteAction],
    }));

    return Toolbars;
}

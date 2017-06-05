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
            var layer = this.editor.location.layer;
            if (layer) {
                var currentEditor = layer.editor;
                if (currentEditor) {
                    if (currentEditor instanceof this.options.type) {
                        BaseToolbarAction.prototype.enable.call(this);
                    }
                } else {
                    BaseToolbarAction.prototype.enable.call(this);
                }
            } else {
                BaseToolbarAction.prototype.enable.call(this);
            }
        }
    });

    var LineControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                tooltip: 'Draw line',
                className: 'cadasta-toolbar draw-polyline',
            },
            subToolbar: new SubToolbar({
                className: 'cancel-draw-line leaflet-subtoolbar',
                actions: [CancelAction],
            }),
            type: L.Editable.PolylineEditor,
        },
        addHooks: function () {
            var layer = this.editor.location.layer;
            if (layer) {
                var currentEditor = layer.editor;
                if (currentEditor) {
                    if (currentEditor.enabled() &&
                        currentEditor instanceof this.options.type) {
                        this.editor.addMulti(this.options.type);
                    }
                } else {
                    this.editor.startPolyline();
                }
            } else {
                this.editor.startPolyline();
            }
        },
    });

    var PolygonControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                tooltip: 'Draw a polygon',
                className: 'cadasta-toolbar draw-polygon',
            },
            subToolbar: new SubToolbar({
                className: 'cancel-draw-poly leaflet-subtoolbar',
                actions: [CancelAction],
            }),
            type: L.Editable.PolygonEditor,
        },
        addHooks: function (e) {
            var layer = this.editor.location.layer;
            if (layer) {
                var currentEditor = layer.editor;
                if (currentEditor) {
                    if (currentEditor.enabled() &&
                        currentEditor instanceof this.options.type) {
                        this.editor.addMulti(e, this.options.type);
                    }
                } else {
                    this.editor.startPolygon();
                }
            } else {
                this.editor.startPolygon();
            }
        },
    });

    var RectangleControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                tooltip: 'Draw a rectangle',
                className: 'cadasta-toolbar draw-rectangle',
            },
            subToolbar: new SubToolbar({
                className: 'cancel-draw-rect leaflet-subtoolbar',
                actions: [CancelAction],
            }),
            type: L.Editable.RectangleEditor,
        },
        addHooks: function () {
            this.editor.startRectangle();
        },
        enable: function () {
            if (this.editor.deleting()) return;
            var layer = this.editor.location.layer;
            if (layer) {
                var currentEditor = layer.editor;
                if (currentEditor && currentEditor instanceof this.options.type) return;
                DrawControl.prototype.enable.call(this);
            } else {
                DrawControl.prototype.enable.call(this);
            }
        }
    });

    var MarkerControl = DrawControl.extend({
        options: {
            toolbarIcon: {
                tooltip: 'Draw marker',
                className: 'cadasta-toolbar draw-marker'
            },
            subToolbar: new SubToolbar({
                className: 'cancel-draw-marker leaflet-subtoolbar',
                actions: [CancelAction],
            }),
            type: L.Editable.MarkerEditor,
        },
        addHooks: function () {
            this.editor.startMarker();
        }
    });



    // edit tools

    var SaveEdit = SubAction.extend({
        options: {
            toolbarIcon: {
                html: 'Save',
                tooltip: 'Save edits',
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
            if (this.editor.deleting()) {
                this.editor.cancelDelete();
            }
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
        enable: function (e) {
            if (this.editor.hasEditableLayer() && !this.editor.deleting()) {
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
            if (this.editor.editing()) {
                this.editor.cancelEdit();
            }
            this.editor.startDelete();
        },
        enable: function () {
            if (this.editor.hasEditableLayer()) {
                L.ToolbarAction.prototype.enable.call(this);
            }
        },
        disable: function () {
            if (this.editor.deleting()) return;
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
            LineControl, PolygonControl,
            RectangleControl, MarkerControl
        ]
    }));

    Toolbars.push(new EditToolbar({
        position: 'topleft',
        className: 'leaflet-smap-edit',
        actions: [EditAction, DeleteAction],
    }));

    return Toolbars;
};

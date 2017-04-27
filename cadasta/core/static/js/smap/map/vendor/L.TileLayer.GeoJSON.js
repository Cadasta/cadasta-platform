// set up webworker object.
var WebWorker = {};
WebWorker.addTileData = function (data, callback) {
    var features = data.geojson.results.features;
    var new_layer = [];
    if (features) {
        for (var i = 0, f_len = features.length; i < f_len; i++) {
            if (features[i].geometries || features[i].geometry || features[i].features || features[i].coordinates) {
                if (!data._loadedfeatures[features[i].id]) {
                    new_layer.push(features[i]);
                    data._loadedfeatures[features[i].id] = true;
                }
            }
        }
    }
    data.new_layer = new_layer;
    callback(data);
};

// Load data tiles from an AJAX data source
L.TileLayer.Ajax = L.TileLayer.extend({
    _requests: [],
    _loadedfeatures: {},
    _tiles: {},
    _ticker: 1,
    _original_request_len: null,
    _addTile: function (tilePoint) {
        var tile = {
            datum: null,
            processed: false
        };
        this._tiles[tilePoint.x + ':' + tilePoint.y] = {
            el: tile,
            coords: {
                x: tilePoint.x,
                y: tilePoint.y,
                z: tilePoint.z
            },
            current: true
        };
        this._loadTile(tile, tilePoint);
    },
    // XMLHttpRequest handler; closure over the XHR object, the layer, and the tile
    _xhrHandler: function (req, layer, tile, tilePoint) {
        return function () {
            if (req.readyState !== 4) {
                return;
            }
            var s = req.status;
            if ((s >= 200 && s < 300 && s != 204) || s === 304) {
                tile.datum = JSON.parse(req.responseText);
                layer._tileLoaded(tile, tilePoint);
            } else {
                layer._tileLoaded(tile, tilePoint);
            }
        };
    },
    // Load the requested tile via AJAX
    _loadTile: function (tile, tilePoint) {
        if (tilePoint.x < 0 || tilePoint.y < 0) {
            return;
        }
        var layer = this;
        var req = new XMLHttpRequest();
        this._requests.push(req);
        req.onreadystatechange = this._xhrHandler(req, layer, tile, tilePoint);
        req.open('GET', this.getTileUrl(tilePoint), true);
        req.send();

        req.addEventListener("loadend", this._loadEnd.bind(this));
    },
    _loadEnd: function () {
        this._original_request_len = this._original_request_len || this._requests.length;
        if (this._ticker < this._original_request_len) {
            this._ticker++;
        } else {
            map.fire('endtileload');
            $('#messages #loading').addClass('hidden');
        }
    },
    _reset: function () {
        L.TileLayer.prototype._reset.apply(this, arguments);
        for (var i = 0; i < this._requests.length; i++) {
            this._requests[i].abort();
        }
        this._requests = [];
    },
    _update: function () {
        if (this._map && this._map._panTransition && this._map._panTransition._inProgress) {
            return;
        }
        if (this._tilesToLoad < 0) {
            this._tilesToLoad = 0;
        }
        L.TileLayer.prototype._update.apply(this, arguments);
    }
});


L.TileLayer.GeoJSON = L.TileLayer.Ajax.extend({
    // Store each GeometryCollection's layer by key, if options.unique function is present
    _keyLayers: {},

    // Used to calculate svg path string for clip path elements
    _clipPathRectangles: {},

    initialize: function (numWorkers, numLocations, url, options, geojsonOptions) {
        this.numWorkers = numWorkers;
        this.numLocations = numLocations;
        this._workers = new Array(this.numWorkers);
        this.messages = {};
        this.queue = { total: numWorkers };

        $('#messages #loading').removeClass('hidden');

        L.TileLayer.Ajax.prototype.initialize.call(this, url, options);

        this.geojsonLayer = new L.GeoJSON(null, geojsonOptions);
    },
    onAdd: function (map) {
        var i = 0;
        this.queue.free = [];
        this.queue.len = 0;
        this.queue.tiles = [];

        while (i < this.numWorkers) {
            this.queue.free.push(i);
            this._workers[i] = catiline(WebWorker);
            i++;
        }

        map.on("zoomstart", function () {
            this.queue.len = 0;
            this.queue.tiles = [];
        }, this);


        this._lazyTiles = new Tile(0, 0, 0, map.maxZoom);
        this._map = map;
        L.TileLayer.Ajax.prototype.onAdd.call(this, map);
        map.addLayer(this.geojsonLayer);
        // map.addLayer(this.features);
    },
    onRemove: function (map) {
        this.messages = {};
        var len = this._workers.length;
        var i = 0;
        while (i < len) {
            this._workers[i]._close();
            i++;
        }

        L.TileLayer.Ajax.prototype.onRemove.call(this, map);

        map.removeLayer(this.geojsonLayer);
        // map.removeLayer(this.features);
    },
    _reset: function () {
        this.geojsonLayer.clearLayers();
        this._keyLayers = {};
        this._removeOldClipPaths();
        L.TileLayer.Ajax.prototype._reset.apply(this, arguments);
    },

    _getUniqueId: function () {
        return String(this._leaflet_id || ''); // jshint ignore:line
    },

    // Remove clip path elements from other earlier zoom levels
    _removeOldClipPaths: function () {
        for (var clipPathId in this._clipPathRectangles) {
            var prefix = clipPathId.split('tileClipPath')[0];
            if (this._getUniqueId() === prefix) {
                var clipPathZXY = clipPathId.split('_').slice(1);
                var zoom = parseInt(clipPathZXY[0], 10);
                if (zoom !== this._map.getZoom()) {
                    var rectangle = this._clipPathRectangles[clipPathId];
                    this._map.removeLayer(rectangle);
                    var clipPath = document.getElementById(clipPathId);
                    if (clipPath !== null) {
                        clipPath.parentNode.removeChild(clipPath);
                    }
                    delete this._clipPathRectangles[clipPathId];
                }
            }
        }
    },

    // Recurse LayerGroups and call func() on L.Path layer instances
    _recurseLayerUntilPath: function (func, layer) {
        if (layer instanceof L.Path) {
            func(layer);
        } else if (layer instanceof L.LayerGroup) {
            // Recurse each child layer
            layer.getLayers().forEach(this._recurseLayerUntilPath.bind(this, func), this);
        }
    },

    _clipLayerToTileBoundary: function (layer, tilePoint) {
        // Only perform SVG clipping if the browser is using SVG
        if (!L.Path.SVG) {
            return;
        }
        if (!this._map) {
            return;
        }

        if (!this._map._pathRoot) {
            this._map._pathRoot = L.Path.prototype._createElement('svg');
            this._map._panes.overlayPane.appendChild(this._map._pathRoot);
        }
        var svg = this._map._pathRoot;

        // create the defs container if it doesn't exist
        var defs = null;
        if (svg.getElementsByTagName('defs').length === 0) {
            defs = document.createElementNS(L.Path.SVG_NS, 'defs');
            svg.insertBefore(defs, svg.firstChild);
        } else {
            defs = svg.getElementsByTagName('defs')[0];
        }

        // Create the clipPath for the tile if it doesn't exist
        var clipPathId = this._getUniqueId() + 'tileClipPath_' + tilePoint.z + '_' + tilePoint.x + '_' + tilePoint.y;
        var clipPath = document.getElementById(clipPathId);
        if (clipPath === null) {
            clipPath = document.createElementNS(L.Path.SVG_NS, 'clipPath');
            clipPath.id = clipPathId;

            // Create a hidden L.Rectangle to represent the tile's area
            var tileSize = this.options.tileSize,
                nwPoint = tilePoint.multiplyBy(tileSize),
                sePoint = nwPoint.add([tileSize, tileSize]),
                nw = this._map.unproject(nwPoint),
                se = this._map.unproject(sePoint);
            this._clipPathRectangles[clipPathId] = new L.Rectangle(new L.LatLngBounds([nw, se]), {
                opacity: 0,
                fillOpacity: 0,
                clickable: false,
                noClip: true
            });
            this._map.addLayer(this._clipPathRectangles[clipPathId]);

            // Add a clip path element to the SVG defs element
            // With a path element that has the hidden rectangle's SVG path string
            var path = document.createElementNS(L.Path.SVG_NS, 'path');
            var pathString = this._clipPathRectangles[clipPathId].getPathString();
            path.setAttribute('d', pathString);
            clipPath.appendChild(path);
            defs.appendChild(clipPath);
        }

        // Add the clip-path attribute to reference the id of the tile clipPath
        this._recurseLayerUntilPath(function (pathLayer) {
            pathLayer._container.setAttribute('clip-path', 'url(' + window.location.href + '#' + clipPathId + ')');
        }, layer);
    },

    _renderTileData: function (geojson, tilePoint, workerID) {
        var msg = {
            geojson: geojson,
            _loadedfeatures: this._loadedfeatures,
            workerID: workerID,
        };

        this._workers[workerID].addTileData(msg).then((function (data) {
            if (data.new_layer.length !== 0) {
                this._loadedfeatures = data._loadedfeatures;
                this.geojsonLayer.addData(data.new_layer);
            }


            if (this.queue.len) {
                this.queue.len--;
                next = this.queue.tiles.shift();
                this._renderTileData(next[0], next[1], data.workerID);
            } else {
                this.queue.free.push(data.workerID);
            }

        }.bind(this)), function (e) { console.log(a); });
    },

    _tileLoaded: function (tile, tilePoint) {
        if (tile.datum === null || this.numLocations === Object.keys(this._loadedfeatures).length) {
            return null;
        }

        if (!this.queue.free.length) {
            this.queue.tiles.push([tile, tilePoint]);
            this.queue.len++;
        } else {
            this._renderTileData(tile.datum, tilePoint, this.queue.free.pop());
            this._lazyTiles.load(tilePoint.x, tilePoint.y, tilePoint.z);
        }
    },

    _loadTile: function (tile, tilePoint) {
        if (!this._lazyTiles.isLoaded(tilePoint.x, tilePoint.y, tilePoint.z)) {



            L.TileLayer.Ajax.prototype._loadTile.call(this, tile, tilePoint);
        }
    },
});

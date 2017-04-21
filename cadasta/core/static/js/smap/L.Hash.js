// Based on leaflet-hash: https://github.com/mlevans/leaflet-hash
(function(window) {
    var HAS_HASHCHANGE = (function() {
        var doc_mode = window.documentMode;
        return ('onhashchange' in window) &&
            (doc_mode === undefined || doc_mode > 7);
    })();

    L.Hash = function(map) {
        this.onHashChange = L.Util.bind(this.onHashChange, this);

        if (map) {
            this.init(map);
        }
    };

    L.Hash.parseHash = function(hash) {
        if (hash.indexOf('#') === 0) {
            hash = hash.substr(1);
        }

        if (hash.includes('coords=')) {
            hash = hash.split('coords=')[1];
            
            var args = hash.split("/");
            if (args.length == 3) {
                var zoom = parseInt(args[0], 10),
                lat = parseFloat(args[1]),
                lon = parseFloat(args[2]);
                if (isNaN(zoom) || isNaN(lat) || isNaN(lon)) {
                    return false;
                } else {
                    return {
                        center: new L.LatLng(lat, lon),
                        zoom: zoom
                    };
                }
            } else {
                return false;
            }
        } else {
            return false;
        }
    };

    L.Hash.formatHash = function(map, hash=null) {
        var center = map.getCenter(),
            zoom = map.getZoom(),
            precision = Math.max(0, Math.ceil(Math.log(zoom) / Math.LN2));

        hash = hash || '#/';

        if (!hash.includes('?')) {
            hash += '?';
        } else if (hash.substr(-1) !== '&') {
            hash += '&';
        }
        return hash + "coords=" + [zoom,
            center.lat.toFixed(precision),
            center.lng.toFixed(precision)
        ].join("/");
    },

    L.Hash.prototype = {
        map: null,
        lastHash: null,

        parseHash: L.Hash.parseHash,
        formatHash: L.Hash.formatHash,

        first_call: true,

        init: function(map) {
            this.map = map;

            // reset the hash
            this.lastHash = null;
            if (window.location.hash.includes('coords=')) {
                this.onHashChange();
            }

            if (!this.isListening) {
                this.startListening();
            }
        },

        removeFrom: function(map) {
            if (this.changeTimeout) {
                clearTimeout(this.changeTimeout);
            }

            if (this.isListening) {
                this.stopListening();
            }

            this.map = null;
        },

        onMapMove: function() {
            // bail if we're moving the map (updating from a hash),
            // or if the map is not yet loaded

            if (this.movingMap || !this.map._loaded) {
                return false;
            }

            var hash = location.hash;
            hash = hash.split('coords=')[0];
            while (hash.substr(-1) === '&' || hash.substr(-1) === '?') {
                hash = hash.substr(0, hash.length - 1);
            }

            var new_hash = this.formatHash(this.map, hash);

            if (this.lastHash != new_hash) {
                location.replace(new_hash);
                this.lastHash = new_hash;
            }
        },

        movingMap: false,
        update: function() {
            var hash = location.hash;

            var parsed = this.parseHash(hash);
            if (parsed) {
                this.movingMap = true;
                // We do not need to set the map view unless it's the first time the page is loaded.
                if (this.first_call) {
                    this.map.setView(parsed.center, parsed.zoom);
                    this.first_call = false;
                }

                this.movingMap = false;
            } else {
                this.onMapMove(this.map);
            }
        },

        // defer hash change updates every 100ms
        // This number needs to be less than the timeout in resizeMap in router_mixins
        changeDefer: 300,
        changeTimeout: null,
        onHashChange: function() {
            // throttle calls to update() so that they only happen every
            // `changeDefer` ms
            if (!this.changeTimeout) {
                var that = this;
                this.changeTimeout = setTimeout(function() {
                    that.update();
                    that.changeTimeout = null;
                }, this.changeDefer);
            }
        },

        isListening: false,
        hashChangeInterval: null,
        startListening: function() {
            this.map.on("moveend", this.onMapMove, this);

            if (HAS_HASHCHANGE) {
                L.DomEvent.addListener(window, "hashchange", this.onHashChange);
            } else {
                clearInterval(this.hashChangeInterval);
                this.hashChangeInterval = setInterval(this.onHashChange, 50);
            }
            this.isListening = true;
        },

        stopListening: function() {
            this.map.off("moveend", this.onMapMove, this);

            if (HAS_HASHCHANGE) {
                L.DomEvent.removeListener(window, "hashchange", this.onHashChange);
            } else {
                clearInterval(this.hashChangeInterval);
            }
            this.isListening = false;
        }
    };
    L.hash = function(map) {
        return new L.Hash(map);
    };
    L.Map.prototype.addHash = function() {
        this._hash = L.hash(this);
    };
    L.Map.prototype.removeHash = function() {
        this._hash.removeFrom();
    };
})(window);
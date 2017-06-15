;(function(window, Math) {
    function Tile(x, y, z, maxLevels, parent) {
        this.x = x;
        this.y = y;
        this.z = z;
        this.loaded = false;
        this.maxLevels = maxLevels || 18;
        this.children = [];
        this.parent = parent || null;
    }

    Tile.prototype.findPathToChild = function (x, y, z) {
        const nleafs = Math.pow(2, z - this.z);
        const l0x = nleafs * this.x;
        const l0y = nleafs * this.y;
        const xleft = (x < l0x + (nleafs / 2));
        const yleft = (y < l0y + (nleafs / 2));
        xt = xleft ? this.x * 2 : this.x * 2 + 1;
        yt = yleft ? this.y * 2 : this.y * 2 + 1;

        if (!this.children.length && this.z < this.maxLevels) {
            this.children = [
                new window.Tile(this.x * 2, this.y * 2, this.z + 1, this.maxLevels, this),
                new window.Tile(this.x * 2, this.y * 2 + 1, this.z + 1, this.maxLevels, this),
                new window.Tile(this.x * 2 + 1, this.y * 2, this.z + 1, this.maxLevels, this),
                new window.Tile(this.x * 2 + 1, this.y * 2 + 1, this.z + 1, this.maxLevels, this)
            ];
        }

        for (var i in this.children) {
            const child = this.children[i];
            if (child.x === x && child.y === y && child.z === z) {
                return child;
            }
        }

        for (var i in this.children) {
            const child = this.children[i];
            if (child.x === xt && child.y === yt) {
                return child;
            }
        }
    }

    Tile.prototype.load = function(x, y, z) {
        if (this.x === x && this.y === y && this.z === z && !this.loaded) {
            this.loaded = true;
            if (this.parent) { this.parent.loadFromChild(); }
        } else {
            const child = this.findPathToChild(x, y, z);
            if (child) {child.load(x, y, z);}
        }
    }

    Tile.prototype.loadFromChild = function() {
        var loaded = true;
        for (var i in this.children) {
            if (!this.children[i].loaded) {
                loaded = false;
            }
        }
        if (loaded) {
            this.loaded = true;
            if (this.parent) { this.parent.loadFromChild(); }
        }
    }

    Tile.prototype.isLoaded = function(x, y, z) {
        if (this.loaded) {
            return true;
        }

        if (this.z === z) {
            return false;
        }

        const child = this.findPathToChild(x, y, z);
        if (child) {
            return child.isLoaded(x, y, z);    
        } else {
            return false;
        }
    }

    window.Tile = Tile;
})(window, Math);

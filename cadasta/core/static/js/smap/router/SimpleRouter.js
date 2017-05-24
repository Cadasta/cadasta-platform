// Based on http://joakim.beng.se/blog/posts/a-javascript-router-in-20-lines.html
function SimpleRouter(map) {
    var routes = CreateRoutes(map);

    function router(force_reload) {
        var async_url = '/async' + location.pathname;
        var hash_path = location.hash.slice(1) || '/';

        // first_load will only be true if the first page landed on is a record without coordinates
        if (!hash_path.includes('/records/') || hash_path.includes('coords=')) {
            rm.setFirstLoad(false);
        }

        if (hash_path.includes('coords=')) {
            hash_path = hash_path.substr(0, hash_path.indexOf('coords=') - 1) || '/';
        }

        // Prevents router from reloading every time the coords changes.
        // force_reload is only true when a detach form is submitted
        if (force_reload === false) {
            if (rm.getLastHashPath() === hash_path || hash_path === '/search') {
                return;
            }
        }

        if (hash_path !== '/') {
            async_url = async_url + hash_path.substr(1);
        }

        // Fail safe in case a hashpath does not contain the final backslash
        if (hash_path.substr(hash_path.length - 1) !== '/' && !hash_path.includes('?')) {
            hash_path += '/';
        }

        var route = routes[hash_path] || null;

        // If route is null, there is an ID in the hash. Remove the record id from hash_path to match key in routes.
        if (!route) {
            var new_hash_path = hash_path.split('/');
            new_hash_path.splice(3, 1);
            new_hash_path = new_hash_path.join('/');
            route = routes[new_hash_path];
        }

        if (!route) {
            console.log('that route was undefined:', window.location.hash);
            window.location.hash = '#/overview';
            return;
        }

        var el = document.getElementById(rm.getRouteElement(route.el));
        var geturl = $.ajax({
            type: "GET",
            url: async_url,
            success: function (response, status, xhr) {
                var permission_error = geturl.getResponseHeader('Permission-Error');
                var anonymous_user = geturl.getResponseHeader('Anonymous-User');
                var location_coords = geturl.getResponseHeader('Coordinates');

                if (location_coords && rm.getFirstLoad()) {
                    rm.setCurrentLocationCoords(location_coords);
                }

                if (permission_error) {
                    if (rm.getLastHashPath() && rm.getLastHashPath() !== '/' && rm.getLastHashPath() !== '/overview/') {
                        history.back();
                    } else if (!window.location.hash.includes('/overview.')) {
                        window.location.hash = "/overview/";
                    }
                    if ($('.alert-warning').length === 0) {
                        $('#messages').append(rm.permissionDenied(permission_error));
                    }
                    return;

                } else if (anonymous_user) {
                    window.location = "/account/login/?next=" + window.location.pathname;

                } else {
                    route.controller();
                    el.innerHTML = response;
                    if (route.eventHook) {
                        route.eventHook();
                    }
                }
                rm.setLastHashPath(hash_path);
            }
        });
    } // end router()
    return {
        router: router,
    };
} // end SimpleRouter()

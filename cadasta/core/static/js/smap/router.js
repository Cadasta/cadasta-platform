// Based on http://joakim.beng.se/blog/posts/a-javascript-router-in-20-lines.html
var SimpleRouter = function(map){
  var rm = RouterMixins;
  routes = new CreateRoutes();

  function router() {
    var hash_path = location.hash.slice(1) || '/';
    console.log(hash_path);
    if (hash_path === '/search') {
      return;
    }

    var async_url = '/async' + location.pathname;

    if (hash_path !== '/') {
      async_url = async_url + hash_path.substr(1) + '/';
    }

    var route = routes[hash_path] ? routes[hash_path] : null;

    // Removes record id from hash_path to match key in routes.
    if (!route) {
      var records = ['/records/location', '/records/relationship'];
      var actions = ['/edit', '/delete', '/resources/add', '/resources/new', '/relationships/new'];
      var new_hash_path;

      for (var i in records) {
        if (hash_path.includes(records[i])) {
          new_hash_path = records[i];
        }
      }

      for (var j in actions) {
        if (hash_path.includes(actions[j])) {
          new_hash_path = new_hash_path + actions[j];
        }
      }

      route = routes[new_hash_path];
    }

    var el = document.getElementById(rm.getRouteElement(route.el));
    $.get(async_url, function(response){
      if (response.includes("alert-warning")) {
        window.location.hash = "/overview";
        if ($('.alert-warning').length === 0) {
          $('#messages').append(rm.permissionDenied());
        }
      } else if (response.includes("!DOCTYPE")) {
        window.location = "/account/login/?next=" + window.location.pathname;
      } else {
        route.controller();
        el.innerHTML = response;
        if (route.eventHook) {
          route.eventHook();
        }
      }
    });
  }

  return {
    router: router,
  };
};

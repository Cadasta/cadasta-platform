$(window).load(function () {
  var js_files = [
    'lazytiles.js',
    'L.TileLayer.GeoJSON.js',
    'map.js'
  ];
  var body = $('body')
  for (i in js_files) {
    body.append($('<script src="/static/js/smap/' + js_files[i] + '"></script>'));
  }
});

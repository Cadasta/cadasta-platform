function select_location(e) {
  window.map.eachLayer(function(layer) {
    if (layer.setStyle) {
      layer.setStyle({
        color: '#03f',
        fillColor: '#03f'
      });
    }
  });
  e.target.setStyle({
    color: '#edaa00',
    fillColor: '#edaa00'
  });
  $('#id_id').val(e.target.feature.id);
  $('#id_spatial_unit_type').parent().addClass('hidden');
}

function handle_draw() {
  $('#id_id').val('');
  $('#id_new_entity').val('on');
  $('#id_spatial_unit_type').parent().removeClass('hidden');
}

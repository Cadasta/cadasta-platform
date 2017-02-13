var CreateRoutes = function(map){
  var routes = {};
  var current_location = null;

  function route(path, controller, eventHook=null) {
    routes[path] = {};
    routes[path].controller = controller;
    routes[path].eventHook = eventHook;
  }

  route('/map', function() {
    hideDetailPannel();
    hideModal();
  });

  route('/overview', function() {
    displayDetailPannel();
    hideModal();
    resetLocationStyle();
    map.fitBounds(options.projectExtent);
  });

  route('/', function() {
    displayDetailPannel();
    hideModal();

    resetLocationStyle();
    map.fitBounds(options.projectExtent);
  });


  // *** SPATIAL RECORDS ***
  route('/records/location', function() {
    displayDetailPannel();
    hideModal();

    if (current_location) {
      centerOnLocation(current_location);
    }
  });

  route('/records/location/new', function() {
    displayDetailPannel(edit=true);
    hideModal();

    // ADD: map editing features
  });

  route('/records/location/edit', function() {
    displayDetailPannel(edit=true);
    hideModal();

    if (current_location) {
      centerOnLocation(current_location);
    }
  });

  route('/records/location/delete', function() {
    // Zoom into project bounds.
    displayDetailPannel();
    return displayModal();
  });

  route('/records/location/resources/add', function() {
    displayDetailPannel();
    return displayModal();
  });

  route('/records/location/resources/new', function() {
    displayDetailPannel();
    return displayModal();
  });

  route('/records/location/relationships/new',
    function() {
      displayDetailPannel();
      return displayModal();

    }, function(path){
      var template = function(party) {
        if (!party.id) {
          return party.text;
        }
        return $(
          '<div class="party-option">' +
          '<strong class="party-name">' + party.text + '</strong>' +
          '<span class="party-type">' + party.element.dataset.type + '</span>' +
          '</div>'
        );
      };
      $("#party-select").select2({
        minimumResultsForSearch: 6,
        templateResult: template,
        theme: "bootstrap",
      });

      $('.datepicker').datepicker({
        yearRange: "c-200:c+200",
        changeMonth: true,
        changeYear: true,
      });

      // /* eslint-env jquery */
      $('#add-party').click(function(){
        $('#select-party').toggleClass('hidden');
        $('#new-item').toggleClass('hidden');
      });

      $('table#select-list tr').click(function(event) {
        const target = $(event.target).closest('tr');
        const relId = target.attr('data-id');
        target.closest('tbody').find('tr.info').removeClass('info');
        target.addClass('info');
        $('input[name="id"]').val(relId);
      });

      response = $("#modal-form").submit(function(e){
        e.preventDefault();
        var data = $(this).serializeArray().reduce(function(obj, item) {
            obj[item.name] = item.value;
            return obj;
        }, {});

        $.ajax({
          method: "POST",
          url: path,
          data: data
        }).done(function(response, status, xhr) {
          console.log(response);
          console.log(xhr.status);
          // console.log(response)
          // document.getElementById("additional_modals").innerHTML = response
        });
      });

      return response;
  });


  // *** RELATIONSHIPS ***
  route('/records/relationship', function() {
    displayDetailPannel();
    hideModal();
  });

   route('/records/relationship/edit', function() {
    displayDetailPannel(edit=true);
    hideModal();
  });

  route('/records/relationship/delete', function() {
    displayDetailPannel();
    return displayModal();
  });

  route('/records/relationship/resources/add', function() {
    displayDetailPannel();
    return displayModal();
  });

  route('/records/relationship/resources/new', function() {
    displayDetailPannel();
    return displayModal();
  });

  // route('/records/relationship/relationships/new', function() {
  //   displayDetailPannel();
  //   return displayModal();
  // });

  function resizeMap() {
    window.setTimeout(function() {
        map.invalidateSize();
      }, 400);
  }

  function displayDetailPannel(edit=false) {
    if ($('.content-single').hasClass('detail-hidden')) {
      $('.content-single').removeClass('detail-hidden');
      resizeMap();
    }

    if (!$('#project-detail').hasClass('detail-edit') && edit) {
      $('#project-detail').addClass('detail-edit');
    } else if (!edit && $('#project-detail').hasClass('detail-edit')) {
      $('#project-detail').removeClass('detail-edit');
    }
  }

  function hideDetailPannel() {
    if (!$('.content-single').hasClass('detail-hidden')) {
      $('.content-single').addClass('detail-hidden');
      resizeMap();
    }
  }

  function displayModal() {
    if (!$("#additional_modals").is(':visible')) {
      $("#additional_modals").modal('show');
    }

    return document.getElementById("additional_modals")
  }

  function hideModal() {
    if ($("#additional_modals").is(':visible')) {
      $("#additional_modals").modal('hide');
    }
  }

  function centerOnLocation(location) {
    var bounds;
    if (typeof(location.getBounds) === 'function'){
      bounds = location.getBounds();
    } else {
      // If the spatial unit is a marker
      var latLngs = [location.getLatLng()];
      bounds = L.latLngBounds(latLngs);
    }

    if (bounds.isValid()){
      map.fitBounds(bounds);
    }

    if (location.setStyle) {
      location.setStyle({color: '#edaa00', fillColor: '#edaa00', weight: 3})
    }
  }

  function setCurrentLocation () {
    map.on("popupopen", function(evt){
      currentPopup = evt.popup;

      $('#spatial-pop-up').click(function(e){
        resetLocationStyle();
        current_location = currentPopup._source
        map.closePopup();
      });
    });
  }

  setCurrentLocation();

  function resetLocationStyle() {
    if (current_location && current_location.setStyle) {
      current_location.setStyle({color: '#3388ff', fillColor: '#3388ff', weight: 2})  
    }
  }

  // function interceptSubmit(path) {
    
  // }

  return routes;
}
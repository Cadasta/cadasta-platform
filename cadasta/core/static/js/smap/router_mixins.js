var state;

var RouterMixins = {
  settings: {
    current_location: {url: null, bounds: null},
    current_relationship: {url: null},
    current_active_tab: 'overview',
    el: {
      'detail': 'project-detail',
      'modal': 'additional-modals',
    },
    forms: {
      'detail': '#detail-form',
      'modal': '#modal-form',
      'location-wizard': '#location-wizard',
    }
  },

  init: function() {
    state = this.settings;
    // this.setCurrentLocation();
  },


  /***************
  DETAIL PANEL VS. MODAL
  ****************/
  resizeMap: function() {
    window.setTimeout(function() {
      map.invalidateSize();
    }, 400);
  },

  displayDetailPanel: function() {
    this.hideModal();
    if ($('.content-single').hasClass('detail-hidden')) {
      $('.content-single').removeClass('detail-hidden');
      this.resizeMap();
    }

    if ($('#' + state.el.detail).hasClass('detail-edit')) {
      $('#' + state.el.detail).removeClass('detail-edit');
    }
  },

  displayEditDetailPanel: function() {
    this.hideModal();
    if ($('.content-single').hasClass('detail-hidden')) {
      $('.content-single').removeClass('detail-hidden');
      this.resizeMap();
    }

    if (!$('#' + state.el.detail).hasClass('detail-edit')) {
      $('#' + state.el.detail).addClass('detail-edit');
    }
  },

  hideDetailPanel: function() {
    this.hideModal();
    if (!$('.content-single').hasClass('detail-hidden')) {
      $('.content-single').addClass('detail-hidden');
      this.resizeMap();
    }
  },

  displayModal: function() {
    if (!$('#' + state.el.modal).is(':visible')) {
      $('#' + state.el.modal).modal('show');
    }
  },

  hideModal: function() {
    if ($('#' + state.el.modal).is(':visible')) {
      $('#' + state.el.modal).modal('hide');
    }
  },


  /***************
  UPDATING THE STATE
  ****************/
  setGeoJsonLayer: function(layer) {
    state.geojsonlayer = layer;
  },

  getRouteElement: function(el) {
    return state.el[el]
  },

  updateCurrentLocation: function(url=null) {
    if (url) {
      if (!state.current_location.url) {
        state.current_location.url = url;
      }

    } else if (state.current_location.url !== window.location.hash) {
      state.current_location.url = window.location.hash;
    }

    this.updateCurrentLocationBounds();
  },

  updateCurrentRelationshipUrl: function() {
    if (state.current_relationship.url !== window.location.hash) {
      state.current_relationship.url = window.location.hash;
    }
  },

  getCurrentLocationUrl: function() {
    return state.current_location.url;
  },

  getCurrentRelationshipUrl: function() {
    return state.current_relationship.url;
  },

  centerOnCurrentLocation: function() {
    if (state.current_location.bounds) {
      var bounds;
      var location = state.current_location.bounds;
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
        location.setStyle({color: '#edaa00', fillColor: '#edaa00', weight: 3});
      }
    }
  },

  resetLocationStyle: function(feature) {
    // before state.current_location is updated, the old state needs to be reset
    if (state.current_location.bounds) {
      if (state.current_location.bounds.setStyle) {
        state.current_location.bounds.setStyle({color: '#3388ff', fillColor: '#3388ff', weight: 2});
      }

      feature = state.current_location.bounds.feature;
      state.current_location.bounds._popup.setContent(this.nonActivePopup(feature));
    }
  },

  updateCurrentLocationBounds: function() {
    var layers = state.geojsonlayer.geojsonLayer._layers
    var url = state.current_location.url || window.location.hash

    for (var i in layers) {
      if (url.includes(layers[i]['feature']['id'])) {
        this.resetLocationStyle();

        state.current_location.bounds = layers[i];
        this.centerOnCurrentLocation()
        map.closePopup();
        layers[i]._popup.setContent(this.activePopup(layers[i].feature));
      }
    }
  },

  activateTab: function(tab) {
    // For the location details page. Tabs are built using bootstrap
    var tab_options = ['overview', 'resources', 'relationships']
    tab_options.splice(tab_options.indexOf(tab), 1);

    $('#' + tab + '-tab').addClass('active');
    $($('#' + tab + '-tab').children()[0]).attr({'aria-expanded':"true"});
    $('#' + tab).addClass('active');

    for (var i in tab_options) {
      $('#' + tab_options[i] + '-tab').removeClass('active');
      $($('#' + tab_options[i] + '-tab').children()[0]).attr({'aria-expanded':"false"});
      $('#' + tab_options[i]).removeClass('active');
    }
  },

  setCurrentActiveTab: function(tab) {
    if (state.current_active_tab !== tab) {
      state.current_active_tab = tab;
    }
  },

  getCurrentActiveTab: function() {
    this.activateTab(state.current_active_tab);
  },

  /***************
  ADDING EVENT HOOKS
  ****************/

  uploadResourceHooks: function() {
    original_file = $('input[name="original_file"]').val();

    if (original_file) {
      $('a.file-link').text(original_file);
      $('a.file-link').attr('download', original_file);
    }

    $('.file-input').change(function(event) {
      var file = event.target.files[0];

      $('a.file-link').on('link:update', function() {
          $('a.file-link').text(file.name);
          $('a.file-link').attr('download', file.name);
      });

      $('input[name="original_file"]').val(file.name);
      $('input[name="details-original_file"]').val(file.name);

      var ext = file.name.split('.').slice(-1)[0];
      var type = file.type || MIME_LOOKUPS[ext];
      $('input[name="mime_type"]').val(type);
    });

    $('a.file-remove').click(function() {
      $('.file-well .errorlist').addClass('hidden');
      $(this).parents('.form-group').removeClass('has-error');
    });
  },

  relationshipHooks: function() {
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

    $('button#add-party').click(function() {
      $('#new_entity_field').val('on');
    });

    $('table#select-list tr').click(function(event) {
      const target = $(event.target).closest('tr');
      const relId = target.attr('data-id');
      target.closest('tbody').find('tr.info').removeClass('info');
      target.addClass('info');
      $('input[name="id"]').val(relId);
    });

    function disableConditionals() {
      $('.party-co').addClass('hidden');
      $('.party-gr').addClass('hidden');
      $('.party-in').addClass('hidden');
      $('.party-co .form-control').prop('disabled', 'disabled');
      $('.party-gr .form-control').prop('disabled', 'disabled');
      $('.party-in .form-control').prop('disabled', 'disabled');
    }

    function enableConditions(val) {
      const types = ['co', 'gr', 'in'];
      types.splice(types.indexOf(val), 1);
      $('.party-' + val).removeClass('hidden');
      $('.party-' + val + ' .form-control').prop('disabled', '');
      for (var i in types) {
        $('.party-' + types[i]).addClass('hidden');
        $('.party-' + types[i] +  '.form-control').prop('disabled', 'disabled');
      }
    }

    function toggleParsleyRequired(val) {
      const typeChoices = ['in', 'gr', 'co'];
      $.each(typeChoices, function(idx, choice) {
        if (val === choice) {
          $.each($('.party-' + val + ' .form-control'), function(idx, value) {
            if (value.hasAttribute('data-parsley-required')) {
              $(value).attr('data-parsley-required', true);
              $(value).prop('required', 'required');
              label = $(value)[0].labels[0];
              $(label).addClass('required')
            }
          });
        } else {
          $.each($('.party-' + choice + ' .form-control'), function(idx, value) {
            if (value.hasAttribute('data-parsley-required')) {
              $(value).attr('data-parsley-required', false);
              $(value).prop('required', '');
              label = $(value)[0].labels[0];
              $(label).addClass('required')
            }
          });
        }
      });
    }

    function toggleStates(val) {
      if (val === '') {
        disableConditionals();
      } else {
        enableConditions(val);
        toggleParsleyRequired(val);
      }
    }

    var val = $('.party-type').val().toLowerCase();
    toggleStates(val);


    $('select.party-type').on('change', function(e) {
      const val = e.target.value.toLowerCase();
      toggleStates(val);
    });

    $('select.party-select').on('change', function(e) {
      toggleStates('');
    });
  },


  /***************
  INTERCEPTING FORM SUBMISSIONS
  ****************/
  formSubmission: function(form_type, success_url, eventHook=null){
    var form = state.forms[form_type] || form_type;
    var parent = this;

    $(form).submit(function(e){
      // if form_type === form, then it was triggered by the detach form.
      if (form_type === form) {
        parent.setCurrentActiveTab('resources');
      }
      e.preventDefault();
      var target = e.originalEvent || e.originalTarget;
      var formaction = $('.submit-btn', target.target ).attr('formAction');

      var data = $(this).serializeArray().reduce(function(obj, item) {
          obj[item.name] = item.value;
          return obj;
      }, {});

      $.ajax({
        method: "POST",
        url: formaction,
        data: data
      }).done(function(response) {
        // Is there a better way to tell if the form fails?
        if (!response.includes('DOCTYPE')) {
          form_type = state.el[form_type] || 'detail';
          var el = document.getElementById(form_type);
          el.innerHTML = response;
          if (eventHook) {
            eventHook();
          }

        } else {
          if (window.location.hash === success_url) {
            sr.router();
          } else {
            window.location.hash = success_url;
            $('#overview-tab').removeClass('active');
            $($('#overview-tab').children()[0]).attr({'aria-expanded':"false"})
            $("#overview").removeClass('active')

            $('#resource-tab').addClass('active');
            $($('#resource-tab').children()[0]).attr({'aria-expanded':"true"})
            $("#resource").addClass('active')
          }
        }
      });
    });
  },

  detachFormSubmission: function(success_url){
    var parent = this;
    $.each($('.detach-form'), function(i, form){
      parent.formSubmission(form, success_url);
    });
  },

  /******************
  EXTRA HTML INSERTS
  ******************/
  permissionDenied: function(){
    return "<div class='alert alert-dismissible alert-warning' role='alert'>" +
           "<button type='button' class='close' data-dismiss='alert' aria-label='Close'>" +
           "<span aria-hidden='true'>×</span>" +
           "</button>" +
           "You don't have permission to view this location." +
           "</div>";
  },

  nonActivePopup: function(feature) {
    return "<div class=\"text-wrap\"><h2><span>Location</span>" +
              feature.properties.type +
            "</h2></div>" +
            "<div class=\"btn-wrap\"><a href='#/" +
              feature.properties.url +
            "' id='spatial-pop-up' class='btn btn-primary btn-sm btn-block'>" +
              options.trans.open +
            "</a></div>"
  },

  activePopup: function(feature) {
    return "<div class=\"text-wrap\"><h2><span>Location</span>" +
              feature.properties.type +
            "</h2></div>" +
            "<div class=\"btn-wrap\"><span class=\"btn-sm btn-block\">" +
              options.trans.current_viewing +
              "</span></div>"
  },
};

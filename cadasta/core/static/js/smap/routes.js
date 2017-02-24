var CreateRoutes = function(){
  'use strict';
  var routes = {};
  var rm = RouterMixins;
  rm.init();

  function route(path, el, controller, eventHook=null) {
    routes[path] = {
      el: el,
      controller: controller,
      eventHook: eventHook
    };
  }

  route('/map', 'detail',
    function() {
      rm.hideDetailPanel();
      rm.hideModal();
  });

  route('/overview', 'detail',
    function() {
      rm.displayDetailPanel();
      rm.resetLocationStyle();
      map.fitBounds(options.projectExtent);
  });

  route('/', 'detail',
    function() {
      rm.displayDetailPanel();
      rm.resetLocationStyle();
      map.fitBounds(options.projectExtent);
  });


  // *** SPATIAL RECORDS ***
  route('/records/location', 'detail',
    function() {
      rm.displayDetailPanel();
      rm.centerOnCurrentLocation();
      rm.updateCurrentLocationUrl();
    },
    function(){
      rm.formSubmission(this.el, rm.getCurrentLocationUrl());
      rm.detachFormSubmission(rm.getCurrentLocationUrl());
  });

  route('/records/location/new', 'detail',
    function() {
      rm.displayEditDetailPanel();
  });

  route('/records/location/edit', 'detail', 
    function() {
      rm.displayEditDetailPanel();
      rm.centerOnCurrentLocation();
    },
    function(){
      rm.formSubmission('location-wizard', rm.getCurrentLocationUrl());
  });

  route('/records/location/delete', 'modal',
    function() {
      rm.displayModal();
    },
    function(){
      rm.formSubmission(this.el, '#/overview');
  });

  route('/records/location/resources/add', 'modal',
    function() {
      rm.displayModal();
    }, 
    function() {
      rm.formSubmission(this.el, rm.getCurrentLocationUrl());
  });

  route('/records/location/resources/new', 'modal', 
    function() {
      rm.displayModal();
    }, 
    function() {
      rm.uploadResourceHooks();
      rm.formSubmission(this.el, rm.getCurrentLocationUrl());
  });

  route('/records/location/relationships/new', 'modal',
    function() {
      rm.displayModal();

    }, function() {
      rm.relationshipHooks();
      rm.formSubmission(this.el, rm.getCurrentLocationUrl());
    });


  // *** RELATIONSHIPS ***
  route('/records/relationship', 'detail',
    function() {
      rm.displayDetailPanel();
    },
    function() {
      rm.updateCurrentLocationUrl($("#current-location").attr('href'));
      rm.updateCurrentRelationshipUrl();
      rm.detachFormSubmission(rm.getCurrentRelationshipUrl());
  });

  route('/records/relationship/edit', 'detail',
    function() {
      rm.displayEditDetailPanel();
    }, function(){
      rm.formSubmission(this.el, rm.getCurrentRelationshipUrl());
  });

  route('/records/relationship/delete', 'modal',
    function() {
      rm.displayModal();
    },
    function(){
      rm.formSubmission(this.el, rm.getCurrentLocationUrl());
  });

  route('/records/relationship/resources/add', 'modal',
    function() {
      rm.displayModal();
    }, function() {
      rm.formSubmission(this.el, rm.getCurrentRelationshipUrl());
  });

  route('/records/relationship/resources/new', 'modal',
    function() {
      rm.displayModal();
    }, function() {
      rm.uploadResourceHooks();
      rm.formSubmission(this.el, rm.getCurrentRelationshipUrl());
  });

  return routes;
};

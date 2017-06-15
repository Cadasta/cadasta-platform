function CreateRoutes(map) {
    'use strict';
    var routes = {};
    window.rm =  RouterMixins();
    window.rm.init();

    function route(path, el, controller, eventHook) {
        routes[path] = {
            el: el,
            controller: controller,
            eventHook: eventHook
        };
    }

    /*********************
    MAP
    *********************/

    route('/map/', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.project_map,
                'display_detail_panel': false,
                'display_modal': false,
                'active_sidebar': 'map',
            });
            map.locationEditor.fire('route:map');
        });

    /*********************
    OVERVIEW
    *********************/

    route('/overview/', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.project_overview,
                'display_detail_panel': true,
                'display_modal': false,
                'active_sidebar': 'overview',

                'reset_current_location': true,
            });
            map.locationEditor.fire('route:overview');
        });

    route('/', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.project_overview,
                'display_detail_panel': true,
                'display_modal': false,
                'active_sidebar': 'overview',
                'reset_current_location': true,
            });
        });


    /**************
    SPATIAL RECORDS
    **************/
    route('/records/location/', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_detail,
                'display_detail_panel': true,
                'display_modal': false,
            });
        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'datatable': true,
                'detach_forms': true,
                'active_tab': 'overview',
            });

            rm.locationDetailHooks();
            map.locationEditor.fire('route:location:detail');
        });

    /*********************
    SPATIAL DETAIL TABS
    *********************/
    route('/records/location/?tab=overview', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_detail,
                'display_detail_panel': true,
                'display_modal': false,
            });
        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'datatable': true,
                'detach_forms': true,
                'active_tab': 'overview',
            });

            rm.locationDetailHooks();
        });

    route('/records/location/?tab=resources', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_detail,
                'display_detail_panel': true,
                'display_modal': false,
            });
        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'datatable': true,
                'detach_forms': true,
                'active_tab': 'resources',
            });

            rm.locationDetailHooks();
        });

    route('/records/location/?tab=relationships', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_detail,
                'display_detail_panel': true,
                'display_modal': false,
            });
        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'datatable': true,
                'detach_forms': true,
                'active_tab': 'relationships',
            });
            rm.locationDetailHooks();
        });

    /*********************
    SPATIAL ACTIONS
    *********************/

    /****** REQUIRES GEOEDITING *************/
    route('/records/location/new/', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_add,
                'display_edit_panel': true,
                'display_modal': false,
            });
            map.locationEditor.fire('route:location:new');
        },
        function () {
            rm.updateState({
                'form': {
                    'type': 'location-wizard',
                    'success_url': 'overview',
                    'callback': rm.locationEditHooks
                }
            });
            rm.locationEditHooks();
        });
    /*******************************************/


    /****** REQUIRES GEOEDITING *************/
    route('/records/location/edit/', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_edit,
                'display_edit_panel': true,
                'display_modal': false,
            });
        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'form': {
                    'type': 'location-wizard',
                    'success_url': 'location',
                    'callback': rm.locationEditHooks
                }
            });
            // trigger editing once tiles finished loading
            var hash_path = window.location.hash.slice(1) || '/';
            var fid = hash_path.split('/')[3];
            map.locationEditor.fire('route:location:edit', { 'fid': fid });
            rm.locationEditHooks();
        });
    /*******************************************/

    route('/records/location/delete/', 'modal',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_delete,
                'display_detail_panel': true,
                'display_modal': true,
            });
        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'form': {
                    'type': 'modal',
                    'success_url': 'overview',
                    'callback': rm.locationDeleteHooks
                },
            });
            rm.locationDeleteHooks();
        });

    /*********************
    SPATIAL RESOURCES
    *********************/

    route('/records/location/resources/add/', 'modal',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_resource_add,
                'display_detail_panel': true,
                'display_modal': true,
            });
        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'active_tab': 'resources',
                'datatable': true,
                'form': {
                    'type': 'modal',
                    'success_url': 'location',
                    'tab': 'resources',
                },
            });
            rm.addResourceHooks();
        });

    route('/records/location/resources/new/', 'modal',
        function () {
            rm.updatePage({
                'page_title': options.trans.location_resource_new,
                'display_detail_panel': true,
                'display_modal': true,
            });
        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'active_tab': 'resources',
                'form': {
                    'type': 'modal',
                    'success_url': 'location',
                    'tab': 'resources',
                    'callback': rm.uploadResourceHooks,
                },
            });

            rm.uploadResourceHooks();
        });

    /*********************
    SPATIAL RELATIONSHIPS
    *********************/

    route('/records/location/relationships/new/', 'modal',
        function () {
            rm.updatePage({
                'page_title': options.trans.rel_add,
                'display_detail_panel': true,
                'display_modal': true,
            });

        },
        function () {
            rm.updateState({
                'current_location': window.location.hash,
                'active_tab': 'relationships',
                'form': {
                    'type': 'modal',
                    'success_url': 'location',
                    'tab': 'relationships',
                    'callback': rm.relationshipAddHooks,
                },
            });
            rm.relationshipAddHooks();
        });

    /*******************
    RELATIONSHIP RECORDS
    *******************/
    route('/records/relationship/', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.rel_detail,
                'display_detail_panel': true,
                'display_modal': false,
            });
        },
        function () {
            rm.updateState({
                'current_location': $("#current-location").attr('href'),
                'current_relationship': window.location.hash,
                'active_tab': 'relationships',
                'datatable': true,
                'detach_forms': true,
            });
            rm.relationshipHooks();
        });

    /*******************
    RELATIONSHIP ACTIONS
    *******************/

    route('/records/relationship/edit/', 'detail',
        function () {
            rm.updatePage({
                'page_title': options.trans.rel_edit,
                'display_edit_panel': true,
                'display_modal': false,
            });
        },
        function () {
            rm.updateState({
                'current_location': $("#current-location").attr('href'),
                'current_relationship': window.location.hash,
                'form': {
                    'type': 'detail',
                    'success_url': 'relationship',
                    'callback': rm.relationshipHooks,
                },
            });
            rm.relationshipHooks();
        });

    route('/records/relationship/delete/', 'modal',
        function () {
            rm.updatePage({
                'page_title': options.trans.rel_delete,
                'display_detail_panel': true,
                'display_modal': true,
            });
        },
        function () {
            rm.updateState({
                'current_relationship': window.location.hash,
                'form': {
                    'type': 'modal',
                    'success_url': 'location',
                    'tab': 'relationships',
                },
            });
        });


    /*********************
    RELATIONSHIP RESOURCES
    *********************/
    route('/records/relationship/resources/add/', 'modal',
        function () {
            rm.updatePage({
                'page_title': options.trans.rel_resource_add,
                'display_detail_panel': true,
                'display_modal': true,
            });
        },
        function () {
            rm.updateState({
                'current_relationship': window.location.hash,
                'datatable': true,
                'form': {
                    'type': 'modal',
                    'success_url': 'relationship',
                },
            });
            rm.addResourceHooks();
        });

    route('/records/relationship/resources/new/', 'modal',
        function () {
            rm.updatePage({
                'page_title': options.trans.rel_resource_new,
                'display_detail_panel': true,
                'display_modal': true,
            });
        },
        function () {
            rm.updateState({
                'current_relationship': window.location.hash,
                'form': {
                    'type': 'modal',
                    'success_url': 'relationship',
                    'callback': rm.uploadResourceHooks,
                },
            });
            rm.uploadResourceHooks();
        });

    return routes;
}

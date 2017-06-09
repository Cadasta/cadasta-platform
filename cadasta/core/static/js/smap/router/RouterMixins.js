var state;

function RouterMixins() {
    return {
        settings: {
            current_location: { url: null, feature: null },
            current_relationship: { url: null },
            el: {
                'detail': 'project-detail',
                'modal': 'additional-modals',
            },
            last_hash: '',
            coords: null,
            first_load: true,
        },

        init: function () {
            state = this.settings;
        },

        updatePage: function (kwargs) {
            if (kwargs.page_title) {
                this.setPageTitle(kwargs.page_title);
            }

            if (kwargs.display_modal) {
                this.displayModal();
            } else {
                this.hideModal();
            }

            if (kwargs.display_detail_panel) {
                this.displayDetailPanel();
            } else {
                this.hideDetailPanel();
            }

            if (kwargs.display_edit_panel) {
                this.displayEditDetailPanel();
            }

            if (kwargs.active_sidebar) {
                this.setSidebar(kwargs.active_sidebar);
            }

            if (kwargs.reset_current_location) {
                // this.resetPreviousLocationStyle();
                if (state.current_location.layer) {
                    Styles.resetStyle(state.current_location.layer);
                }
            }
        },

        updateState: function (kwargs) {
            /*********
            'current_location': String. where to find the url for the location connected to the record. Location detail pages will pull from the window.location.hash, Relationship detail pages will pull from the #current-location link
            *********/
            if (kwargs.current_location) {
                this.setCurrentLocationUrl(kwargs.current_location);
                this.setCurrentLocationFeature();
            }

            /*********
            'current_relationship': String. where to find the the url for the relationship connected to the record. Relationship detail pages will pull from the window.location.hash.
            *********/
            if (kwargs.current_relationship) {
                this.setCurrentRelationshipUrl(kwargs.current_relationship);
            }

            /*********
            'datatable': Boolean. Does the page contain a DataTable?
            *********/
            if (kwargs.datatable) {
                dataTableHook();
            }

            /*********
            'active_tab': S1['overview', 'relationships', 'resources']. Choose which of the bootstrap tabs in the Location Detail page you want activated.
            *********/
            if (kwargs.active_tab) {
                rm.activateTab(kwargs.active_tab);
            }

            /*********
            'detach_forms': Boolean. Does the page contain a Datatable with resources that can be detached?
            *********/
            if (kwargs.detach_forms) {
                this.detachFormSubmission();
            }

            /*********
            'form': {
              'type': ['modal', 'detail'] Does the form appear in the detail panel, or does a modal appear?

              'success_url': ['relationship', 'location'] Does the page need to redirect to a location or relationship detail page?

              'tab': [null, 'overview', 'resources', 'relationships'] If the success url redirects to a Location Detail page, is there a specific tab you want activated?

              'callback': [null, rm.relationshipHooks, rm.uploadResourcesHooks] Did you call any event hooks after updateState? If the form fails, you'll need to call them again after the form is submitted.
            }
            *********/
            if (kwargs.form) {
                var success_url = this.getSuccessUrl(
                    kwargs.form.success_url,
                    kwargs.form.tab
                );
                rm.formSubmission(kwargs.form.type, success_url, kwargs.form.callback);
            }

        },

        /***************
        DOM MANIPULATION
        ****************/
        resizeMap: function (size) {
            size = size || 300;
            $('#project-map').height(size);

            window.setTimeout(function () {
                map.invalidateSize();
            }, 500);
        },

        displayDetailPanel: function () {
            if ($('.content-single').hasClass('detail-hidden')) {
                $('.content-single').removeClass('detail-hidden');
                this.resizeMap();
            }
            
            if ($('#' + state.el.detail).hasClass('detail-edit')) {
                $('#' + state.el.detail).removeClass('detail-edit');
            }
        },

        displayEditDetailPanel: function () {
            if ($('.content-single').hasClass('detail-hidden')) {
                $('.content-single').removeClass('detail-hidden');
                this.resizeMap();
            }

            if (!$('#' + state.el.detail).hasClass('detail-edit')) {
                $('#' + state.el.detail).addClass('detail-edit');
            }
        },

        hideDetailPanel: function () {
            if (!$('.content-single').hasClass('detail-hidden')) {
                $('.content-single').addClass('detail-hidden');
                this.resizeMap($(window).height() - 30);
            }
        },

        displayModal: function () {
            if (!$('#' + state.el.modal).is(':visible')) {
                $('#' + state.el.modal).modal('show');
            }
        },

        hideModal: function () {
            if ($('#' + state.el.modal).is(':visible')) {
                $('#' + state.el.modal).modal('hide');
            }
        },

        // Only useful if multiple sidebar buttons lead to the map
        setSidebar: function (sidebar_button) {
            if (!$('#sidebar').hasClass(sidebar_button)) {
                $('#sidebar').removeClass().addClass(sidebar_button);
            }
        },

        activateTab: function (tab) {
            // For the location details page. Tabs are built using bootstrap
            var tab_options = ['overview', 'resources', 'relationships'];
            tab_options.splice(tab_options.indexOf(tab), 1);

            $('#' + tab + '-tab').addClass('active');
            $($('#' + tab + '-tab').children()[0]).attr({ 'aria-expanded': "true" });
            $('#' + tab).addClass('active');

            for (var i in tab_options) {
                $('#' + tab_options[i] + '-tab').removeClass('active');
                $($('#' + tab_options[i] + '-tab').children()[0]).attr({ 'aria-expanded': "false" });
                $('#' + tab_options[i]).removeClass('active');
            }
        },

        setPageTitle: function (new_title) {
            var page_title = $('head title').context.title;

            if (!page_title.includes(new_title)) {
                page_title = page_title.split('|');
                page_title.splice(1, 1, new_title);
                page_title = page_title.join('|');

                $('head title').context.title = page_title;
            }
        },

        /***************
        UPDATING THE STATE
        ****************/
        setGeoJsonLayer: function (layer) {
            state.geojsonlayer = layer;
        },

        getRouteElement: function (el) {
            return state.el[el];
        },

        setCurrentRelationshipUrl: function (url) {
            if (!url.includes(state.current_relationship.url)) {
                url = url.split('/');
                state.current_relationship.url = '#/records/relationship/' + url[3] + '/';
            }

            return state.current_relationship.url;
        },

        getCurrentRelationshipUrl: function () {
            return state.current_relationship.url;
        },

        setCurrentLocationUrl: function (url) {
            if (!url.includes(state.current_location.url)) {
                url = url.split('/');
                state.current_location.url = '#/records/location/' + url[3] + '/';
            }

            return state.current_location.url;
        },

        getCurrentLocationUrl: function () {
            return state.current_location.url;
        },

        getCurrentLocationLayer: function () {
            return state.current_location.layer;
        },

        setCurrentLocationFeature: function () {
            var url = state.current_location.url;

            if (!url) return;

            if (state.current_location.layer) {
                if (url.includes(state.current_location.layer.feature.id)) {
                    Styles.setSelectedStyle(state.current_location.layer);
                    editor.setEditable(state.current_location.layer.feature, state.current_location.layer);

                    if (window.location.hash.includes('/edit/')) {
                        map.locationEditor.fire('route:location:edit', { 'fid': state.current_location.layer.feature.id });
                    }

                    return;
                }
            }

            var layers = state.geojsonlayer.geojsonLayer._layers;
            var found = false;

            for (var i in layers) {
                if (!isNaN(layers[i].feature.id)) {
                    var new_url = url.substr(2);
                    new_url = new_url.substr(0, new_url.length -1);
                    layer_id = new_url.split('/')[2];

                    layers[i].feature.id = layer_id;
                    layers[i].feature.properties.url = new_url;
                }
                if (url.includes(layers[i].feature.id)) {
                    found = true;
                    Styles.resetStyle(state.current_location.layer);

                    state.current_location.layer = layers[i];
                    Styles.setSelectedStyle(layers[i]);
                    editor.setEditable(state.current_location.layer.feature, state.current_location.layer);

                    if (window.location.hash.includes('/edit/')) {
                        map.locationEditor.fire('route:location:edit', { 'fid': layers[i].feature.id });
                    }
                    return;
                }
            }


        },

        setCurrentLocationCoords: function (coords) {
            coords = coords.replace('(', '').replace(')', '').split(',');
            state.coords = [
                [coords[0], coords[1]],
                [coords[2], coords[3]]
            ];

            map.fitBounds(state.coords);
            state.first_load = false;
        },

        // Checked to prevent router from firing with each coords change.
        setLastHashPath: function (hash) {
            state.last_hash = hash;
        },

        getLastHashPath: function () {
            return state.last_hash;
        },

        // Checked to see if this is the first time the page has loaded, and if we need to zoom on a location.
        setFirstLoad: function (val) {
            if (state.first_load != val) {
                state.first_load = val;
            }
        },

        getFirstLoad: function () {
            return state.first_load;
        },

        getSuccessUrl: function (type, tab) {
            url = '';
            if (type === 'overview') {
                return '#/overview/';
            }

            if (type === 'location') {
                url = rm.getCurrentLocationUrl() ? rm.getCurrentLocationUrl() : rm.setCurrentLocationUrl();
            } else if (type === 'relationship') {
                url = rm.getCurrentRelationshipUrl() ? rm.getCurrentRelationshipUrl() : rm.setCurrentRelationshipUrl();
            }
            if (url.substr(url.length - 1) !== '/') {
                url += '/';
            }

            url = tab ? url + '?tab=' + tab : url;

            return url;
        },

        /***************
        ADDING EVENT HOOKS
        ****************/

        addEventScript: function (file) {
            scripts = $('script[src="/static/js/' + file + '"]');
            if (scripts.length) {
                $.each(scripts, function (i) {
                    scripts[i].parentElement.removeChild(scripts[i]);
                });
            }

            $('body').append($('<script type="text/javascript" src="/static/js/' + file + '"></script>'));
        },

        uploadResourceHooks: function () {
            rm.addEventScript('file-upload.js');
        },

        addResourceHooks: function () {
            rm.addEventScript('script_add_lib.js');
        },

        datepickerHooks: function() {
            $('.datepicker').datepicker({
                yearRange: "c-200:c+200",
                changeMonth: true,
                changeYear: true,
            });
        },

        locationDeleteHooks: function () {
            $('#delete-location').on('click', function (e) {
                editor.fire('location:delete');
            });
        },

        locationFormButtons: function () {
            $('.btn-default.cancel').on('click', function (e) {
                editor.dispose();
            });

            $('button[name="submit-button"]').on('click', function (e) {
                e.preventDefault();
                editor.save(final = true);
                $('#location-wizard').submit();
            });
        },

        requiredFieldHooks: function (name) {
            $.each($('input[name^="' + name + '"]'), function(idx, input) {
                if (input.hasAttribute('data-parsley-required')) {
                    $(input).prev('label').addClass('required');
                }
            });
        },

        relationshipHooks: function () {
            rm.addEventScript('rel_tenure.js');
            rm.addEventScript('party_attrs.js');

            var template = function (party) {
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

            rm.datepickerHooks();
            rm.requiredFieldHooks('tenurerelationship');
        },

        locationEditHooks: function () {
            rm.requiredFieldHooks('spatial');
            rm.datepickerHooks();
            rm.locationFormButtons();
        },

        locationDetailHooks: function () {
            function formatHashTab(tab) {
                var hash = window.location.hash;
                var coords = '';

                if (hash.includes('coords=')) {
                    coords = hash.substr(hash.indexOf('coords='));
                    hash = hash.substr(0, hash.indexOf('coords=') - 1);
                }

                if (hash.includes('?tab=' + tab)) {
                    return;
                }

                if (hash.includes('?tab=')) {
                    hash = hash.split('?tab=')[0];
                }

                hash = hash + '?tab=' + tab;

                if (coords) {
                    hash = hash + '&' + coords;
                }

                window.location.hash = hash;
                rm.activateTab(tab);
            }

            $('#resources-tab').click(function () {
                formatHashTab('resources');
            });

            $('#overview-tab').click(function () {
                formatHashTab('overview');
            });

            $('#relationships-tab').click(function () {
                formatHashTab('relationships');
            });
        },

        /***************
        INTERCEPTING FORM SUBMISSIONS
        ****************/
        formSubmission: function (form_type, success_url, eventHook) {
            success_url = success_url || null;
            var form_type_options = {
                'detail': '#detail-form',
                'modal': '#modal-form',
                'location-wizard': '#location-wizard',
            };

            var form = form_type_options[form_type] || form_type;
            var detach = false;

            // if form_type is a complete form and not just an id, it came from detachFormSubmission
            if (form === form_type) {
                detach = true;
            }

            $(form).submit(function (e) {
                e.preventDefault();
                var target = e.originalEvent || e.originalTarget || e.target;
                var formaction = $('.submit-btn', target.target).attr('formaction');
                $('.submit-btn', target.target).prop({ 'disabled': true });

                var data = $(this).serializeArray().reduce(function (obj, item) {
                    obj[item.name] = item.value;
                    return obj;
                }, {});

                // prevents error caused by submiting a 'location edit' form
                // after deleting the geometry.
                if (data.geometry && data.geometry.includes('[[null]]')) {
                    data.geometry = 'None';
                }


                var posturl = $.ajax({
                    method: "POST",
                    url: formaction,
                    data: data,
                    success: function (response, status, xhr) {
                        form_error = posturl.getResponseHeader('Form-Error');
                        if (form_error) {
                            el_type = state.el[form_type] || 'project-detail';
                            var el = document.getElementById(el_type);
                            el.innerHTML = response;

                            rm.formSubmission(form_type, success_url, eventHook);
                            if (eventHook) {
                                eventHook();
                            }

                        } else if (typeof response === 'object' && 'new_location_id' in response) {
                            window.location.replace('#/records/location/' + response.new_location_id + '/');
                        } else {
                            if (detach) {
                                sr.router(true);
                            } else {
                                window.location.replace(success_url);
                            }
                        }
                    }
                });
            });
        },

        detachFormSubmission: function () {
            $.each($('.detach-form'), (function (i, form) {
                this.formSubmission(form);
            }).bind(this));

            if ($('.paginate_button').length) {
                $('.paginate_button.next').on('click', (function (i, button) {
                    this.detachFormSubmission();
                }).bind(this));
                $('.paginate_button.previous').on('click', (function (i, button) {
                    this.detachFormSubmission();
                }).bind(this));
            }
        },

        /******************
        EXTRA HTML TEMPLATES
        ******************/
        permissionDenied: function (error) {
            return "<div class='alert alert-dismissible alert-warning' role='alert'>" +
                "<button type='button' class='close' data-dismiss='alert' aria-label='Close'>" +
                "<span aria-hidden='true'>×</span>" +
                "</button>" + error + "</div>";
        },

        nonActivePopup: function (feature) {
            return "<div class=\"text-wrap\"><h2><span>Location</span>" +
                feature.properties.type +
                "</h2></div>" +
                "<div class=\"btn-wrap\"><a href='#/" +
                feature.properties.url + '/' +
                "' id='spatial-pop-up' class='btn btn-primary btn-sm btn-block'>" +
                options.trans.open +
                "</a></div>";
        },

        activePopup: function (feature) {
            return "<div class=\"text-wrap\"><h2><span>Location</span>" +
                feature.properties.type +
                "</h2></div>" +
                "<div class=\"btn-wrap\"><span class=\"btn-sm btn-block\">" +
                options.trans.current_viewing +
                "</span></div>";
        },
    };
}

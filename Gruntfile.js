module.exports = function(grunt) {
    grunt.initConfig({
        pkg: grunt.file.readJSON('cadasta/core/package.json'),

        dirs: {
            core: 'cadasta/core/static/js',

            smap: {
                index:  '<%= dirs.core %>/smap',
                map:    '<%= dirs.core %>/smap/map',
                edit:   '<%= dirs.core %>/smap/edit',
                router: '<%= dirs.core %>/smap/router',

                all: ['<%= dirs.smap.index %>/*.js',
                      '<%= dirs.smap.edit %>/*.js',
                      '<%= dirs.smap.router %>/*.js',
                      '<%= dirs.smap.map %>/*.js']
            },
        },

        jshint: {
          files: [
          'Gruntfile.js',
          '<%= dirs.smap.index %>/*.js',
          '<%= dirs.smap.map %>/*.js',
          '<%= dirs.smap.router %>/*.js',
          '<%= dirs.smap.edit %>/*.js',
          '<%= dirs.core %>/*.js',
          ],
          options: {
            globals: {
              jQuery: true
            }
          }
        },

        concat: {
            options: {
              separator: ';\n',
              banner: '/*! Cadasta <%= grunt.template.today("dd-mm-yyyy") %> */\n\n\n',
              sourceMap: {
                includeSources: true,
              },
              sourceMapName: '<%= dirs.smap.index %>/dist/smap.min.js.map',
            },
            dist: {
               src: [
                '<%= dirs.smap.map %>/vendor/catiline.js', 
                '<%= dirs.smap.map %>/vendor/lazytiles.js', 
                '<%= dirs.smap.map %>/vendor/L.TileLayer.GeoJSON.js', 
                '<%= dirs.smap.map %>/map.js', 
                '<%= dirs.smap.edit %>/vendor/Leaflet.Editable.js',
                '<%= dirs.smap.edit %>/vendor/leaflet.toolbar.js',
                '<%= dirs.smap.edit %>/controls.js',
                '<%= dirs.smap.edit %>/tooltip.js',
                '<%= dirs.smap.edit %>/editor.js',
                '<%= dirs.smap.edit %>/vendor/LatLngUtil.js',
                '<%= dirs.smap.edit %>/styles.js',
                '<%= dirs.smap.edit %>/vendor/path.drag.js',
                '<%= dirs.smap.router %>/vendor/L.Hash.js',
                '<%= dirs.smap.router %>/RouterMixins.js', 
                '<%= dirs.smap.router %>/CreateRoutes.js',
                '<%= dirs.smap.router %>/SimpleRouter.js',
                '<%= dirs.smap.index %>/index.js'],

               dest: '<%= dirs.smap.index %>/dist/smap.min.js',
            },
        },

        uglify: {
            options: {
                sourceMap: {
                  includeSources: true,
                },
                sourceMapIn: '<%= dirs.smap.index %>/dist/smap.min.js.map',
                mangle: true,
                banner: '/*! Cadasta <%= grunt.template.today("dd-mm-yyyy") %> */\n'
            },
            app: {
                src: ['<%= concat.dist.dest %>'],
                dest: '<%= dirs.smap.index %>/dist/smap.min.js'
            }
        },

        watch: {
            options: {
                livereload: true
            },
            javascript: {
                files: '<%= dirs.smap.all %>',
                tasks: ['concat', 'uglify']
            }
        }
    });

    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-concat');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.registerTask('default', ['concat', 'uglify', 'jshint']);
    grunt.registerTask('runserver', ['concat', 'uglify', 'watch']);
    grunt.registerTask('production', ['concat', 'uglify']);
};

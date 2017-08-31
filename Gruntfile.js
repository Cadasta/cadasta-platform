module.exports = function(grunt) {
  grunt.initConfig({
    babel: {
      options: {
        sourceMap: true,
        presets: ['es2015'],
        plugins: ['transform-react-jsx']
      },
      dist: {
        files: {
          'cadasta/core/static/dist/PaginatedTable.js': 'cadasta/core/static/jsx/PaginatedTable/PaginatedTable.jsx',
          'cadasta/core/static/dist/PartyRow.js': 'cadasta/core/static/jsx/PaginatedTable/PartyRow.jsx'
        }
      }
    },
    uglify: {
      build: {
        files: [{
          expand: true,
          cwd: 'cadasta/core/static/dist',
          src: '*.js',
          dest: 'cadasta/core/static/dist',
          rename: function (dst, src) {
            return dst + '/' + src.replace('.js', '.min.js');
          }
        }]
      }
    },
    eslint: {
      target: ['cadasta/core/static/jsx/**/*.jsx']
    }
  });

  grunt.loadNpmTasks('grunt-babel');
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-eslint');

  grunt.registerTask('build', ['babel', 'uglify']);
  grunt.registerTask('lint', ['eslint']);
};

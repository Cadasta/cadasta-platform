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
          'cadasta/core/static/dist/paginated-table.js': 'cadasta/core/static/jsx/PaginatedTable/PaginatedTable.jsx'
        }
      }
    },
    uglify: {
      build: {
        src: 'cadasta/core/static/dist/paginated-table.js',
        dest: 'cadasta/core/static/dist/paginated-table.min.js'
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

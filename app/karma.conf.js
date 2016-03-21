const webpack = require('webpack');
const BUILD_OPTIONS = require('./config/webpack.options').BUILD_OPTIONS;
const LOADERS = require('./config/webpack.loaders');

module.exports = function karmaConf(config) {
  config.set({
    frameworks: ['mocha', 'chai', 'sinon'],
    files: [
      'test/index.js',
    ],
    preprocessors: {
      'test/index.js': ['webpack', 'sourcemap'],
    },
    webpack: {
      resolve: {
        alias: {
          sinon: 'sinon/pkg/sinon',
        },
        modulesDirectories: ['node_modules'],
        extensions: ['', '.jsx', '.js', '.json'],
      },
      node: {
        fs: 'empty',
      },
      devtool: 'inline-source-map',
      cache: true,
      module: {
        noParse: [
          /node_modules\/sinon\//,
        ],
        loaders: LOADERS,
      },
      plugins: [
        new webpack.DefinePlugin(BUILD_OPTIONS),
      ],
      externals: {
        'jsdom': 'window',
        'cheerio': 'window',
        'react/lib/ExecutionEnvironment': true,
        'react/lib/ReactContext': true,
      },
    },
    webpackMiddleware: {
      quiet: true,
      watchOptions: {
        poll: true
      }
    },
    browsers: ['jsdom'],
    hostname: '0.0.0.0',
    reporters: ['dots'],
    colors: true,
    plugins: [
      'karma-chai',
      'karma-mocha',
      'karma-sinon',
      'karma-sourcemap-loader',
      'karma-webpack',
      'karma-jsdom-launcher',
    ],
  });
};

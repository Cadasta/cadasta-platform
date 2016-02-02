module.exports = function karmaConf(config) {
  config.set({
    frameworks: ['mocha', 'chai', 'sinon'],
    files: [
      'test/test_index.js',
    ],
    preprocessors: {
      'test/test_index.js': ['webpack', 'sourcemap'],
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
        loaders: [
          {
            exclude: /(vendor|node_modules)/,
            test: /\.jsx?$/,
            loader: 'babel-loader',
          },
          {
            test: /\.po$/,
            loader: 'po-catalog-loader',
            query: {
              referenceExtensions: ['.js', '.jsx'],
            },
          },
          {
            test: /\.json$/,
            loader: 'json-loader',
          },
        ],
      },
      externals: {
        'jsdom': 'window',
        'cheerio': 'window',
        'react/lib/ExecutionEnvironment': true,
      },
    },
    browsers: ['jsdom'],
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

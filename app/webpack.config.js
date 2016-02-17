const webpack = require('webpack');
const path = require('path');
const BUILD_OPTIONS = require('./config/webpack.options').BUILD_OPTIONS;
const LOADERS = require('./config/webpack.loaders');

process.argv.forEach(function processCliArgs(arg) {
  if (arg.startsWith('--build')) {
    const options = arg.split('=')[1].split(',');

    options.forEach(function processOption(option) {
      const optionKey = '__' + option.toUpperCase() + '__';
      BUILD_OPTIONS[optionKey] = true;
    });
  }
});

module.exports = {
  entry: [
    './src/index.jsx',
  ],
  module: {
    loaders: LOADERS,
  },
  resolve: {
    extensions: ['', '.js', '.jsx'],
    root: [
      path.resolve('./src'),
    ],
  },
  output: {
    path: __dirname + '/dist',
    publicPath: '/',
    filename: 'bundle.js',
  },
  devServer: {
    contentBase: './dist',
    hot: true,
    historyApiFallback: true,
  },
  plugins: [
    new webpack.HotModuleReplacementPlugin(),
    new webpack.DefinePlugin(BUILD_OPTIONS),
  ],
};

const webpack = require('webpack');
const path = require('path');
const BUILD_OPTIONS = require('./webpack.options').BUILD_OPTIONS;

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
    loaders: [{
      test: /\.jsx?$/,
      exclude: /node_modules/,
      loader: 'react-hot!babel',
    }, {
      test: /\.po$/,
      loader: 'po-catalog-loader',
      query: {
        referenceExtensions: ['.js', '.jsx'],
      },
    }, {
      test: /\.json?$/,
      exclude: /node_modules/,
      loader: 'react-hot!json',
    }, {
      test: /\.scss$/,
      loaders: ['style', 'css', 'sass'],
    }, {
      test: /\.(jpe?g|png|gif|svg)$/i,
      loader: 'file-loader?name=img/[name].[ext]',
    }, {
      test: /\.(woff|woff2|eot|ttf|svg)$/,
      loader: 'file-loader?name=fonts/[name].[ext]',
    }],
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

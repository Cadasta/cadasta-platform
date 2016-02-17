module.exports = [
  {
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
  },
];

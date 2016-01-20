import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';

import store from './js/store';
import router from './js/router';

ReactDOM.render(
  <Provider store={store}>
    { router }
  </Provider>,
  document.getElementById('cadasta')
);

import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';

import makeStore from './store';
import router from './router';

const store = makeStore();

ReactDOM.render(
  <Provider store={store}>
    { router }
  </Provider>,
  document.getElementById('cadasta')
);

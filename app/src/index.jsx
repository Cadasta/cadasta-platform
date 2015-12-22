import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import Router, { Route } from 'react-router';

import { AppContainer } from './components/App';
import { HomeContainer } from './components/home';
import makeStore from './store';

const store = makeStore();

const routes = <Route component={AppContainer}>
  <Route path="/" component={HomeContainer} />
</Route>;

ReactDOM.render(
  <Provider store={store}>
    <Router>{routes}</Router>
  </Provider>,
  document.getElementById('cadasta')
);
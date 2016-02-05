import React from 'react';
import Router from 'react-router/lib/Router';
import Route from 'react-router/lib/Route';
import IndexRoute from 'react-router/lib/IndexRoute';

import history from './history';


import { AppContainer } from './core/components/App';
import { DashboardContainer } from './core/components/Dashboard';
import { HomeContainer } from './core/components/Home';
import account, { checkAuth, requireAuth } from './account/routes';


const router = (
  <Router history={ history } >
    <Route path="/" component={ AppContainer } >
      <IndexRoute component={ HomeContainer } onEnter={ checkAuth } />
      <Route path="/dashboard/" component={ DashboardContainer } onEnter={ requireAuth } />
      { account }
    </Route>
  </Router>
);

export default router;

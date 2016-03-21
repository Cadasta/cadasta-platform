import React from 'react';
import { Router, Route, browserHistory, IndexRoute } from 'react-router';

import { AppContainer } from './core/components/App';
import { DashboardContainer } from './core/components/Dashboard';
import { HomeContainer } from './core/components/Home';
import account, { checkAuth, requireAuth } from './account/routes';


const router = (
  <Router history={ browserHistory } >
    <Route path="/" component={ AppContainer } >
      <IndexRoute component={ HomeContainer } onEnter={ checkAuth } />
      <Route path="/dashboard/" component={ DashboardContainer } onEnter={ requireAuth } />
      { account }
    </Route>
  </Router>
);

export default router;

import React from 'react';
import Router, { Route, IndexRoute } from 'react-router';

import history from '../history';


import { AppContainer } from '../components/App';
import { DashboardContainer } from '../components/Home/Dashboard';
import { HomeContainer } from '../components/Home';
import account, { checkAuth, requireAuth } from './account';


const router = <Router history={ history } >
  <Route path="/" component={ AppContainer } >
    <IndexRoute component={ HomeContainer } onEnter={ checkAuth } />
    <Route path="/dashboard/" component={ DashboardContainer } onEnter={ requireAuth } />
    { account }
  </Route>
</Router>;

export default router;

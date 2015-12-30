import React from 'react';
import Router, { Route } from 'react-router';

import history from './history'
import { AppContainer } from './components/App';
import { LoginContainer } from './components/Account/Login';
import { LogoutContainer } from './components/Account/Logout';


const router = <Router history={ history }>
  <Route path="/" component={ AppContainer }>
    <Route path="/account/login/" component={ LoginContainer } />
    <Route path="/account/logout/" component={ LogoutContainer } />
  </Route>
</Router>;

export default router;

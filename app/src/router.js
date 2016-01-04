import React from 'react';
import Router, { Route, IndexRoute } from 'react-router';

import history from './history';
import store from './store';
import { accountGetUserInfo } from './actions/account';
import { AppContainer } from './components/App';
import { HomeContainer } from './components/Home';
import { LoginContainer } from './components/Account/Login';
import { LogoutContainer } from './components/Account/Logout';
import { ProfileContainer } from './components/Account/Profile';
import { PasswordContainer } from './components/Account/Password';
import { PasswordResetContainer } from './components/Account/PasswordReset';
import { PasswordResetConfirmContainer } from './components/Account/PasswordResetConfirm';
import { ActivateContainer } from './components/Account/Activate';
import { DashboardContainer } from './components/Home/Dashboard';


function recoverAuthToken() {
  let auth_token = store.getState().get('user').get('auth_token');

  if (!auth_token) {
    if (window.localStorage.getItem('auth_token')) {
      auth_token = window.localStorage.getItem('auth_token');
    }

    if (auth_token) {
      store.dispatch({
        type: 'POST_LOGIN_DONE',
        response: {auth_token}
      });
      store.dispatch(accountGetUserInfo());
    }
  }

  return auth_token ? true : false;
}


function checkAuth(nextState, replaceState) {
  if (recoverAuthToken()) {
    replaceState(null, '/dashboard/');
  }
}


function requireAuth(nextState, replaceState) {
  if (!recoverAuthToken()) {
    replaceState({nextPathname: nextState.location.pathname}, '/account/login/');
  }
}


const router = <Router history={ history }>
  <Route path="/" component={ AppContainer } >
    <IndexRoute component={ HomeContainer } onEnter={ checkAuth } />
    <Route path="/account/login/" component={ LoginContainer } />
    <Route path="/account/logout/" component={ LogoutContainer } />
    <Route path="/account/profile/" component={ ProfileContainer } onEnter={ requireAuth } />
    <Route path="/account/password/" component={ PasswordContainer } onEnter={ requireAuth } />
    <Route path="/account/password/reset/" component={ PasswordResetConfirmContainer } onEnter={ requireAuth } />
    <Route path="/account/password/reset/confirm/:uid/:token/" component={ PasswordResetConfirmContainer } onEnter={ requireAuth } />
    <Route path="/account/activate/:uid/:token/" component={ ActivateContainer } />
    <Route path="/dashboard/" component={ DashboardContainer } onEnter={ requireAuth } />
  </Route>
</Router>;

export default router;

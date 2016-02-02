import React from 'react';
import Route from 'react-router/lib/Route';

import store from '../store';

import { accountGetUserInfo } from './actions';
import { LoginContainer } from './components/Login';
import { LogoutContainer } from './components/Logout';
import { ProfileContainer } from './components/Profile';
import { RegisterContainer } from './components/Register';
import { PasswordContainer } from './components/Password';
import { PasswordResetContainer } from './components/PasswordReset';
import { PasswordResetConfirmContainer } from './components/PasswordResetConfirm';
import { ActivateContainer } from './components/Activate';

function recoverAuthToken() {
  let authToken = store.getState().user.get('auth_token');

  if (!authToken) {
    authToken = window.sessionStorage.getItem('auth_token') ||
      window.localStorage.getItem('auth_token');

    if (authToken) {
      store.dispatch({
        type: 'SET_TOKEN',
        response: { auth_token: authToken },
      });
      store.dispatch(accountGetUserInfo());
    }
  }

  return authToken ? true : false;
}


export function checkAuth(nextState, replaceState) {
  if (recoverAuthToken()) {
    replaceState(null, '/dashboard/');
  }
}


export function requireAuth(nextState, replaceState) {
  if (!recoverAuthToken()) {
    replaceState({ nextPathname: nextState.location.pathname }, '/account/login/');
  }
}

export default (
  <div>
    <Route path="/account/login/" component={ LoginContainer } />
    <Route path="/account/logout/" component={ LogoutContainer } onEnter={ requireAuth } />
    <Route path="/account/register/" component={ RegisterContainer } />
    <Route path="/account/profile/" component={ ProfileContainer } onEnter={ requireAuth } />
    <Route path="/account/password/" component={ PasswordContainer } onEnter={ requireAuth } />
    <Route
      path="/account/password/reset/"
      component={ PasswordResetContainer }
      onEnter={ requireAuth }
    />
    <Route
      path="/account/password/reset/confirm/:uid/:token/"
      component={ PasswordResetConfirmContainer }
      onEnter={ requireAuth }
    />
    <Route path="/account/activate/:uid/:token/" component={ ActivateContainer } />
  </div>
);

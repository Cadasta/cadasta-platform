import React from 'react';
import { Route } from 'react-router';

import store from '../store';

import { accountGetUserInfo } from '../actions/account';
import { LoginContainer } from '../components/Account/Login';
import { LogoutContainer } from '../components/Account/Logout';
import { ProfileContainer } from '../components/Account/Profile';
import { RegisterContainer } from '../components/Account/Register';
import { PasswordContainer } from '../components/Account/Password';
import { PasswordResetContainer } from '../components/Account/PasswordReset';
import { PasswordResetConfirmContainer } from '../components/Account/PasswordResetConfirm';
import { ActivateContainer } from '../components/Account/Activate';

function recoverAuthToken() {
  let auth_token = store.getState().user.get('auth_token');

  if (!auth_token) {
    auth_token = window.sessionStorage.getItem('auth_token') || window.localStorage.getItem('auth_token')

    if (auth_token) {
      store.dispatch({
        type: 'SET_TOKEN',
        response: {auth_token}
      });
      store.dispatch(accountGetUserInfo());
    }
  }

  return auth_token ? true : false;
}


export function checkAuth(nextState, replaceState) {
  if (recoverAuthToken()) {
    replaceState(null, '/dashboard/');
  }
}


export function requireAuth(nextState, replaceState) {
  if (!recoverAuthToken()) {
    replaceState({nextPathname: nextState.location.pathname}, '/account/login/');
  }
}

export default (
  <div>
    <Route path="/account/login/" component={ LoginContainer } />
    <Route path="/account/logout/" component={ LogoutContainer } onEnter={ requireAuth } />
    <Route path="/account/register/" component={ RegisterContainer } />
    <Route path="/account/profile/" component={ ProfileContainer } onEnter={ requireAuth } />
    <Route path="/account/password/" component={ PasswordContainer } onEnter={ requireAuth } />
    <Route path="/account/password/reset/" component={ PasswordResetContainer } onEnter={ requireAuth } />
    <Route path="/account/password/reset/confirm/:uid/:token/" component={ PasswordResetConfirmContainer } onEnter={ requireAuth } />
    <Route path="/account/activate/:uid/:token/" component={ ActivateContainer } />
  </div>
)
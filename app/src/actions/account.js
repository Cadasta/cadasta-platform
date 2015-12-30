import fetch from 'isomorphic-fetch';

import SETTINGS from '../settings';
import history from '../history';

export const POST_LOGIN_START = 'POST_LOGIN_START';
export const POST_LOGIN_DONE  = 'POST_LOGIN_DONE';

export const POST_LOGOUT_START = 'POST_LOGOUT_START';
export const POST_LOGOUT_DONE  = 'POST_LOGOUT_DONE';

export const POST_REGISTER_START = 'POST_REGISTER_START';
export const POST_REGISTER_DONE  = 'POST_REGISTER_DONE';

export const POST_UPDATEPROFILE_START = 'POST_UPDATEPROFILE_START';
export const POST_UPDATEPROFILE_DONE  = 'POST_UPDATEPROFILE_DONE';

export const GET_USERINFO_START = 'GET_USERINFO_START';
export const GET_USERINFO_DONE  = 'GET_USERINFO_DONE';


export function postLoginStart() {
  return {
    type: POST_LOGIN_START
  }
}

export function postLoginDone(response) {
  return {
    type: POST_LOGIN_DONE,
    response
  }
}

export function accountLogin(userCredentials) {
  return dispatch => {
    dispatch(postLoginStart());

    return fetch(SETTINGS.API_BASE + '/account/login/', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userCredentials)
    })
      .then(response => response.json())
      .then(json => {
        dispatch(postLoginDone(json));
        dispatch(accountGetUserInfo());
      });
  }
}

export function postLogoutStart() {
  return {
    type: POST_LOGOUT_START
  }
}

export function postLogoutDone(response) {
  return {
    type: POST_LOGOUT_DONE,
    response
  }
}

export function accountLogout() {
  return dispatch => {
    dispatch(postLogoutStart());

    return fetch(SETTINGS.API_BASE + '/account/logout/', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + window.localStorage.auth_token
      },
      body: JSON.stringify({})
    })
      .then(response => {
        if (response.status === 200) return {};
      })
      .then(json => dispatch(postLogoutDone(json)));
  } 
}

export function postRegisterStart() {
  return {
    type: POST_REGISTER_START
  }
}

export function postRegisterDone(response) {
  return {
    type: POST_REGISTER_DONE,
    response
  }
}

export function accountRegister(userCredentials) {
  return dispatch => {
    dispatch(postRegisterStart());

    return fetch(SETTINGS.API_BASE + '/account/register/', {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userCredentials)
    })
      .then(response => {
        if (response.status === 201) {
          history.replaceState(null, '/account/login/');
        }

        return response.json();
      })
      .then(json => {
        dispatch(postRegisterDone(json));
      });
  }
}

export function getUserInfoStart() {
  return {
    type: GET_USERINFO_START
  }
}

export function getUserInfoDone(response) {
  return {
    type: GET_USERINFO_DONE,
    response
  }
}

export function accountGetUserInfo() {
  return dispatch => {
    dispatch(getUserInfoStart());


    console.log(window.localStorage.getItem('auth_token'))
    return fetch(SETTINGS.API_BASE + '/account/me/', {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + window.localStorage.getItem('auth_token')
      }
    })
      .then(response => response.json())
      .then(json => dispatch(getUserInfoDone(json)));
  }
}

export function postUpdateProfileStart() {
  return {
    type: POST_UPDATEPROFILE_START
  }
}

export function postUpdateProfileDone(response) {
  return {
    type: POST_UPDATEPROFILE_DONE,
    response
  }
}

export function accountUpdateProfile(userCredentials) {
  return dispatch => {
    dispatch(postUpdateProfileStart());

    return fetch(SETTINGS.API_BASE + '/account/me/', {
      method: 'PUT',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': 'Token ' + window.localStorage.getItem('auth_token')
      },
      body: JSON.stringify(userCredentials)
    })
      .then(response => response.json())
      .then(json => dispatch(postUpdateProfileDone(json)));
  }
}

import Request from '../request';

import { requestStart, requestDone } from './messages';
import { redirect } from './router';


export const POST_LOGIN_SUCCESS  = 'POST_LOGIN_SUCCESS';
export const POST_LOGIN_ERROR  = 'POST_LOGIN_ERROR';
export const POST_LOGOUT_SUCCESS  = 'POST_LOGOUT_SUCCESS';
export const POST_REGISTER_SUCCESS  = 'POST_REGISTER_SUCCESS';
export const POST_REGISTER_ERROR  = 'POST_REGISTER_ERROR';
export const POST_UPDATEPROFILE_SUCCESS  = 'POST_UPDATEPROFILE_SUCCESS';
export const POST_UPDATEPROFILE_ERROR  = 'POST_UPDATEPROFILE_ERROR';
export const GET_USERINFO_SUCCESS  = 'GET_USERINFO_SUCCESS';
export const POST_CHANGEPASSWORD_SUCCESS  = 'GET_CHANGEPASSWORD_SUCCESS';
export const POST_CHANGEPASSWORD_ERROR = 'POST_CHANGEPASSWORD_ERROR';
export const POST_RESETPASSWORD_SUCCESS  = 'GET_RESETPASSWORD_SUCCESS';
export const POST_RESETCONFIRMPASSWORD_SUCCESS  = 'GET_RESETCONFIRMPASSWORD_SUCCESS';
export const POST_ACTIVATE_SUCCESS  = 'GET_ACTIVATE_SUCCESS';

/* ********************************************************
 *
 * Login
 *
 * ********************************************************/

export function postLoginSuccess(response) {
  return {
    type: POST_LOGIN_SUCCESS,
    response
  }
}

export function postLoginError(response) {
  return {
    type: POST_LOGIN_ERROR,
    response
  }
}

export function accountLogin(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/login/', userCredentials, false)
      .then(
        (success => {
          var redirectTo = (userCredentials.redirectTo ? userCredentials.redirectTo : '/dashboard/');
          dispatch(postLoginSuccess(success, redirectTo));
          dispatch(requestDone());
          dispatch(redirect(redirectTo));
          dispatch(accountGetUserInfo());
        }),
        (error => {
          dispatch(postLoginError(error));
          dispatch(requestDone());
        })
      );
  }
}

/* ********************************************************
 *
 * Logout
 *
 * ********************************************************/

export function postLogoutSuccess() {
  return {
    type: POST_LOGOUT_SUCCESS
  }
}

export function accountLogout() {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/logout/')
      .then(
        (success => {
          dispatch(postLogoutSuccess(success));
          dispatch(requestDone());
        })
      )
  } 
}

/* ********************************************************
 *
 * Register user
 *
 * ********************************************************/

export function postRegisterSuccess(response) {
  return {
    type: POST_REGISTER_SUCCESS,
    response
  }
}

export function postRegisterError(response) {
  return {
    type: POST_REGISTER_ERROR,
    response
  }
}

export function accountRegister(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/register/', userCredentials, false)
      .then(
        (success => {
          dispatch(postRegisterSuccess(success));
          dispatch(requestDone());
          dispatch(redirect('/account/login/'));
        }),
        (error => {
          dispatch(postRegisterError(error));
          dispatch(requestDone());
          dispatch(redirect('/account/register/'));
        })
      )
  }
}

/* ********************************************************
 *
 * Get user information
 *
 * ********************************************************/

export function getUserInfoSuccess(response) {
  return {
    type: GET_USERINFO_SUCCESS,
    response
  }
}

export function accountGetUserInfo() {
  return dispatch => {
    dispatch(requestStart());

    return Request.get('/account/me/')
      .then(
        (json => {
          dispatch(getUserInfoSuccess(json));
          dispatch(requestDone());
        })
      )
  }
}

/* ********************************************************
 *
 * Update profile
 *
 * ********************************************************/

export function postUpdateProfileSuccess(response) {
  return {
    type: POST_UPDATEPROFILE_SUCCESS,
    response
  }
}

export function postUpdateProfileError(response) {
  return {
    type: POST_UPDATEPROFILE_ERROR,
    response
  }
}

export function accountUpdateProfile(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.put('/account/me/', userCredentials)
      .then(
        (success => {
          dispatch(postUpdateProfileSuccess(success));
          dispatch(requestDone());
        }),
        (error => {
          dispatch(postUpdateProfileError(error));
          dispatch(requestDone());
        })
      )
  }
}


/* ********************************************************
 *
 * Change password
 *
 * ********************************************************/

export function postChangePasswordSuccess() {
  return {
    type: POST_CHANGEPASSWORD_SUCCESS
  }
}

export function postChangePasswordError(response) {
  return {
    type: POST_CHANGEPASSWORD_ERROR,
    response
  }
}

export function accountChangePassword(passwords) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/password/', passwords)
      .then(
        (success => {
          dispatch(postChangePasswordSuccess());
          dispatch(requestDone());
        }),
        (error => {
          dispatch(postChangePasswordError(error));
          dispatch(requestDone());
        })
      )
  }
}

/* ********************************************************
 *
 * Reset password
 *
 * ********************************************************/

export function postResetPasswordSuccess() {
  return {
    type: POST_RESETPASSWORD_SUCCESS
  }
}

export function accountResetPassword(tokens) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/password/reset/', tokens)
      .then(
        (json => {
          dispatch(postResetPasswordSuccess(json));
          dispatch(requestDone());
        })
      )
  }
}

/* ********************************************************
 *
 * Confirm reset password
 *
 * ********************************************************/

export function postResetConfirmPasswordSuccess() {
  return {
    type: POST_RESETCONFIRMPASSWORD_SUCCESS
  }
}

export function accountResetConfirmPassword(password) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/password/reset/confirm/', password)
      .then(
        (json => {
          dispatch(postResetConfirmPasswordSuccess(json));
          dispatch(requestDone());
        })  
      )
  }
}

/* ********************************************************
 *
 * Activate account
 *
 * ********************************************************/

export function postActivateSuccess() {
  return {
    type: POST_ACTIVATE_SUCCESS
  }
}

export function accountActivate(data) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/activate/', data)
      .then(
        (json => {
          dispatch(postActivateSuccess());
          dispatch(requestDone());
          dispatch(redirect('/account/login/'));
        })
      )
  }
}

import Request from '../request';

import { requestStart, requestDone } from './messages';
import { redirect } from './router';


export const LOGIN_SUCCESS  = 'LOGIN_SUCCESS';
export const LOGIN_ERROR  = 'LOGIN_ERROR';

export const LOGOUT_SUCCESS  = 'LOGOUT_SUCCESS';
export const LOGOUT_ERROR  = 'LOGOUT_ERROR';

export const REGISTER_SUCCESS  = 'REGISTER_SUCCESS';
export const REGISTER_ERROR  = 'REGISTER_ERROR';

export const UPDATEPROFILE_SUCCESS  = 'UPDATEPROFILE_SUCCESS';
export const UPDATEPROFILE_ERROR  = 'UPDATEPROFILE_ERROR';

export const USERINFO_SUCCESS  = 'USERINFO_SUCCESS';
export const USERINFO_ERROR  = 'USERINFO_ERROR';

export const CHANGEPASSWORD_SUCCESS  = 'CHANGEPASSWORD_SUCCESS';
export const CHANGEPASSWORD_ERROR = 'CHANGEPASSWORD_ERROR';

export const RESETPASSWORD_SUCCESS  = 'RESETPASSWORD_SUCCESS';
export const RESETPASSWORD_ERROR  = 'RESETPASSWORD_ERROR';

export const RESETCONFIRMPASSWORD_SUCCESS  = 'RESETCONFIRMPASSWORD_SUCCESS';
export const RESETCONFIRMPASSWORD_ERROR  = 'RESETCONFIRMPASSWORD_ERROR';

export const ACTIVATE_SUCCESS  = 'ACTIVATE_SUCCESS';
export const ACTIVATE_ERROR  = 'ACTIVATE_ERROR';

/* ********************************************************
 *
 * Login
 *
 * ********************************************************/

export function postLoginSuccess(response, rememberMe) {
  return {
    type: LOGIN_SUCCESS,
    response,
    rememberMe
  }
}

export function postLoginError(response) {
  return {
    type: LOGIN_ERROR,
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
          dispatch(postLoginSuccess(success, userCredentials.rememberMe));
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
    type: LOGOUT_SUCCESS
  }
}

export function postLogoutError(response) {
  return {
    type: LOGOUT_ERROR,
    response
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
        }),
        (error => {
          dispatch(postLogoutError(error));
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
    type: REGISTER_SUCCESS,
    response
  }
}

export function postRegisterError(response) {
  return {
    type: REGISTER_ERROR,
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
          dispatch(accountLogin(userCredentials))
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
    type: USERINFO_SUCCESS,
    response,
    keepMessages: true
  }
}

export function getUserInfoError(response) {
  return {
    type: USERINFO_ERROR,
    response,
    keepMessages: true
  }
}

export function accountGetUserInfo() {
  return dispatch => {
    dispatch(requestStart());

    return Request.get('/account/')
      .then(
        (success => {
          dispatch(getUserInfoSuccess(success));
          dispatch(requestDone());
        }),
        (error => {
          dispatch(getUserInfoError(error));
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
    type: UPDATEPROFILE_SUCCESS,
    response
  }
}

export function postUpdateProfileError(response) {
  return {
    type: UPDATEPROFILE_ERROR,
    response
  }
}

export function accountUpdateProfile(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.put('/account/', userCredentials)
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
    type: CHANGEPASSWORD_SUCCESS
  }
}

export function postChangePasswordError(response) {
  return {
    type: CHANGEPASSWORD_ERROR,
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
    type: RESETPASSWORD_SUCCESS
  }
}

export function postResetPasswordError(response) {
  return {
    type: RESETPASSWORD_ERROR,
    response
  }
}

export function accountResetPassword(tokens) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/password/reset/', tokens)
      .then(
        (success => {
          dispatch(postResetPasswordSuccess(success));
          dispatch(requestDone());
        }),
        (error => {
          dispatch(postResetPasswordError(error));
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
    type: RESETCONFIRMPASSWORD_SUCCESS
  }
}

export function postResetConfirmPasswordError(response) {
  return {
    type: RESETCONFIRMPASSWORD_ERROR,
    response
  }
}

export function accountResetConfirmPassword(password) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/password/reset/confirm/', password)
      .then(
        (success => {
          dispatch(postResetConfirmPasswordSuccess(success));
          dispatch(requestDone());
        }),
        (error => {
          dispatch(postResetConfirmPasswordError(error));
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
    type: ACTIVATE_SUCCESS
  }
}

export function postActivateError(response) {
  return {
    type: ACTIVATE_ERROR,
    response
  }
}

export function accountActivate(data) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post('/account/activate/', data, false)
      .then(
        (success => {
          dispatch(postActivateSuccess());
          dispatch(requestDone());
        }),
        (error => {
          dispatch(postActivateError(error));
          dispatch(requestDone());
        })
      )
  }
}

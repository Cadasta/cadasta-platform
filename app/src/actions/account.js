import Request from '../request';
import history from '../history';

import { requestStart, requestDone } from './messages';


export const POST_LOGIN_SUCCESS  = 'POST_LOGIN_SUCCESS';
export const POST_LOGOUT_SUCCESS  = 'POST_LOGOUT_SUCCESS';
export const POST_REGISTER_SUCCESS  = 'POST_REGISTER_SUCCESS';
export const POST_UPDATEPROFILE_SUCCESS  = 'POST_UPDATEPROFILE_SUCCESS';
export const GET_USERINFO_SUCCESS  = 'GET_USERINFO_SUCCESS';
export const POST_CHANGEPASSWORD_SUCCESS  = 'GET_CHANGEPASSWORD_SUCCESS';
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

export function accountLogin(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/login/',
      (json => {
        dispatch(postLoginSuccess(json));
        dispatch(requestDone());
        dispatch(accountGetUserInfo());

        if (userCredentials.redirectTo) {
          history.replaceState(null, userCredentials.redirectTo);
        } else {
          history.replaceState(null, '/dashboard/');  
        }
      }),
      userCredentials,
      false
    )
  }
}

/* ********************************************************
 *
 * Logout
 *
 * ********************************************************/

export function postLogoutSuccess(response) {
  return {
    type: POST_LOGOUT_SUCCESS,
    response
  }
}

export function accountLogout() {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/logout/',
      (json => {
        dispatch(postLogoutSuccess(json));
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

export function accountRegister(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/register/',
      (json => {
        history.replaceState(null, '/account/login/');
        dispatch(postRegisterSuccess(json));
        dispatch(requestDone());
      }),
      userCredentials,
      false
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

    return Request.get(
      '/account/me/',
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

export function accountUpdateProfile(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.put(
      '/account/me/',
      (json => {
        dispatch(postUpdateProfileSuccess(json));
        dispatch(requestDone());
      }),
      userCredentials
    )
  }
}


/* ********************************************************
 *
 * Change password
 *
 * ********************************************************/

export function postChangePasswordSuccess(response) {
  return {
    type: POST_CHANGEPASSWORD_SUCCESS,
    response
  }
}

export function accountChangePassword(passwords) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/password/',
      (json => {
        dispatch(postChangePasswordSuccess(json));
        dispatch(requestDone());
      }),
      passwords
    )
  }
}

/* ********************************************************
 *
 * Reset password
 *
 * ********************************************************/

export function postResetPasswordSuccess(response) {
  return {
    type: POST_RESETPASSWORD_SUCCESS,
    response
  }
}

export function accountResetPassword(tokens) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/password/reset/',
      (json => {
        dispatch(postResetPasswordSuccess(json));
        dispatch(requestDone());
      }),
      tokens
    )
  }
}

/* ********************************************************
 *
 * Confirm reset password
 *
 * ********************************************************/

export function postResetConfirmPasswordSuccess(response) {
  return {
    type: POST_RESETCONFIRMPASSWORD_SUCCESS,
    response
  }
}

export function accountResetConfirmPassword(password) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/password/reset/confirm/',
      (json => {
        dispatch(postResetConfirmPasswordSuccess(json));
        dispatch(requestDone());
      }),
      password
    )
  }
}

/* ********************************************************
 *
 * Activate account
 *
 * ********************************************************/

export function postActivateSuccess(response) {
  return {
    type: POST_ACTIVATE_SUCCESS,
    response
  }
}

export function accountActivate(data) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/activate/',
      (json => {
        history.replaceState(null, '/account/login/');
        dispatch(postActivateSuccess(json));
        dispatch(requestDone());
      }),
      data
    )
  }
}

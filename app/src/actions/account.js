import Request from '../request';
import history from '../history';

import { requestStart, requestDone } from './messages';


export const POST_LOGIN_DONE  = 'POST_LOGIN_DONE';
export const POST_LOGOUT_DONE  = 'POST_LOGOUT_DONE';
export const POST_REGISTER_DONE  = 'POST_REGISTER_DONE';
export const POST_UPDATEPROFILE_DONE  = 'POST_UPDATEPROFILE_DONE';
export const GET_USERINFO_DONE  = 'GET_USERINFO_DONE';
export const POST_CHANGEPASSWORD_DONE  = 'GET_CHANGEPASSWORD_DONE';
export const POST_RESETPASSWORD_DONE  = 'GET_RESETPASSWORD_DONE';
export const POST_RESETCONFIRMPASSWORD_DONE  = 'GET_RESETCONFIRMPASSWORD_DONE';
export const POST_ACTIVATE_DONE  = 'GET_ACTIVATE_DONE';


/* ********************************************************
 *
 * Login
 *
 * ********************************************************/

export function postLoginDone(response) {
  return {
    type: POST_LOGIN_DONE,
    response
  }
}

export function accountLogin(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/login/',
      (json => {
        dispatch(postLoginDone(json));
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

export function postLogoutDone(response) {
  return {
    type: POST_LOGOUT_DONE,
    response
  }
}

export function accountLogout() {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/logout/',
      (json => {
        dispatch(postLogoutDone(json));
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

export function postRegisterDone(response) {
  return {
    type: POST_REGISTER_DONE,
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
        dispatch(postRegisterDone(json));
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

export function getUserInfoDone(response) {
  return {
    type: GET_USERINFO_DONE,
    response
  }
}

export function accountGetUserInfo() {
  return dispatch => {
    dispatch(requestStart());

    return Request.get(
      '/account/me/',
      (json => {
        dispatch(getUserInfoDone(json));
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

export function postUpdateProfileDone(response) {
  return {
    type: POST_UPDATEPROFILE_DONE,
    response
  }
}

export function accountUpdateProfile(userCredentials) {
  return dispatch => {
    dispatch(requestStart());

    return Request.put(
      '/account/me/',
      (json => {
        dispatch(postUpdateProfileDone(json));
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

export function postChangePasswordDone(response) {
  return {
    type: POST_CHANGEPASSWORD_DONE,
    response
  }
}

export function accountChangePassword(passwords) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/password/',
      (json => {
        dispatch(postChangePasswordDone(json));
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

export function postResetPasswordDone(response) {
  return {
    type: POST_RESETPASSWORD_DONE,
    response
  }
}

export function accountResetPassword(tokens) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/password/reset/',
      (json => {
        dispatch(postResetPasswordDone(json));
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

export function postResetConfirmPasswordDone(response) {
  return {
    type: POST_RESETCONFIRMPASSWORD_DONE,
    response
  }
}

export function accountResetConfirmPassword(password) {
  return dispatch => {
    dispatch(requestStart());

    return Request.post(
      '/account/password/reset/confirm/',
      (json => {
        dispatch(postResetConfirmPasswordDone(json));
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

export function postActivateDone(response) {
  return {
    type: POST_ACTIVATE_DONE,
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
        dispatch(postActivateDone(json));
        dispatch(requestDone());
      }),
      data
    )
  }
}

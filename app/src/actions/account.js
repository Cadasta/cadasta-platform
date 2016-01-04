import Request from '../request';
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

export const POST_CHANGEPASSWORD_START = 'GET_CHANGEPASSWORD_START';
export const POST_CHANGEPASSWORD_DONE  = 'GET_CHANGEPASSWORD_DONE';

export const POST_RESETPASSWORD_START = 'GET_RESETPASSWORD_START';
export const POST_RESETPASSWORD_DONE  = 'GET_RESETPASSWORD_DONE';

export const POST_RESETCONFIRMPASSWORD_START = 'GET_RESETCONFIRMPASSWORD_START';
export const POST_RESETCONFIRMPASSWORD_DONE  = 'GET_RESETCONFIRMPASSWORD_DONE';

export const POST_ACTIVATE_START = 'GET_ACTIVATE_START';
export const POST_ACTIVATE_DONE  = 'GET_ACTIVATE_DONE';


/* ********************************************************
 *
 * Login
 *
 * ********************************************************/


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

    return Request.post(
      '/account/login/',
      (json => {
        console.log(json)
        dispatch(postLoginDone(json));
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

    return Request.post(
      '/account/logout/',
      (json => dispatch(postLogoutDone(json)))
    )
  } 
}

/* ********************************************************
 *
 * Register user
 *
 * ********************************************************/

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

    return Request.post(
      '/account/register/',
      (json => {
        history.replaceState(null, '/account/login/');
        dispatch(postRegisterDone(json));
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

    return Request.get(
      '/account/me/',
      (json => dispatch(getUserInfoDone(json)))
    )
  }
}

/* ********************************************************
 *
 * Update profile
 *
 * ********************************************************/

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

    return Request.put(
      '/account/me/',
      (json => dispatch(postUpdateProfileDone(json))),
      userCredentials
    )
  }
}


/* ********************************************************
 *
 * Change password
 *
 * ********************************************************/

export function postChangePasswordStart() {
  return {
    type: POST_CHANGEPASSWORD_START
  }
}

export function postChangePasswordDone(response) {
  return {
    type: POST_CHANGEPASSWORD_DONE,
    response
  }
}

export function accountChangePassword(passwords) {
  return dispatch => {
    dispatch(postChangePasswordStart());

    return Request.post(
      '/account/password/',
      (json => dispatch(postChangePasswordDone(json))),
      passwords
    )
  }
}

/* ********************************************************
 *
 * Reset password
 *
 * ********************************************************/

export function postResetPasswordStart() {
  return {
    type: POST_RESETPASSWORD_START
  }
}

export function postResetPasswordDone(response) {
  return {
    type: POST_RESETPASSWORD_DONE,
    response
  }
}

export function accountResetPassword(tokens) {
  return dispatch => {
    dispatch(postResetPasswordStart());

    return Request.post(
      '/account/password/reset/',
      (json => dispatch(postResetPasswordDone(json))),
      tokens
    )
  }
}

/* ********************************************************
 *
 * Confirm reset password
 *
 * ********************************************************/

export function postResetConfirmPasswordStart() {
  return {
    type: POST_RESETCONFIRMPASSWORD_START
  }
}

export function postResetConfirmPasswordDone(response) {
  return {
    type: POST_RESETCONFIRMPASSWORD_DONE,
    response
  }
}

export function accountResetConfirmPassword(password) {
  return dispatch => {
    dispatch(postResetConfirmPasswordStart());

    return Request.post(
      '/account/password/reset/confirm/',
      (json => dispatch(postResetConfirmPasswordDone(json))),
      password
    )
  }
}

/* ********************************************************
 *
 * Activate account
 *
 * ********************************************************/

 export function postActivateStart() {
  return {
    type: POST_ACTIVATE_START
  }
}

export function postActivateDone(response) {
  return {
    type: POST_ACTIVATE_DONE,
    response
  }
}

export function accountActivate(data) {
  return dispatch => {
    dispatch(postActivateStart());

    return Request.post(
      '/account/activate/',
      (json => {
        history.replaceState(null, '/account/login/');
        dispatch(postActivateDone(json));
      }),
      data
    )
  }
}

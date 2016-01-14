import { Map, List } from 'immutable';
import { createMessage } from '../utils/messages';

const DEFAULT_STATE = Map({
  requestsPending: 0,
  userFeedback: List([])
});

const ERROR_MESSAGES = {
  LOGIN_ERROR: "Unable to login with provided username and password.",
  LOGOUT_ERROR: "Unable to logout.",
  CHANGEPASSWORD_ERROR: "Unable to change password.",
  REGISTER_ERROR: "Unable to register with provided credentials.",
  UPDATEPROFILE_ERROR: "Unable to update profile.",
  USERINFO_ERROR: "Unable to get user profile information from server.",
  RESETPASSWORD_ERROR: "Unable to reset password.",
  RESETCONFIRMPASSWORD_ERROR: "Unable to reset password.",
  ACTIVATE_ERROR: "Unable to activate account."
}

const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: "Successfully logged in.",
  LOGOUT_SUCCESS: "Successfully logged out.",
  CHANGEPASSWORD_SUCCESS: "Successfully changed password.",
  REGISTER_SUCCESS: "Successfully registered. You can now log in.",
  UPDATEPROFILE_SUCCESS: "Successfully updated profile information.",
  RESETPASSWORD_SUCCESS: "Password successfully reset. Check your inbox for a link to confirm the reset.",
  RESETCONFIRMPASSWORD_SUCCESS: "Password successfully reset.",
  ACTIVATE_SUCCESS: "Account successfully activated."
}

export default function messages(state = DEFAULT_STATE, action) {
  if (action.type in SUCCESS_MESSAGES) {
  
    var message = createMessage('success', SUCCESS_MESSAGES[action.type])
    var userFeedback = state.get('userFeedback').push(message);
    return state.set('userFeedback', userFeedback);

  } else if (action.type in ERROR_MESSAGES) {
  
    var message = createMessage('error', ERROR_MESSAGES[action.type], action.response)
    var userFeedback = state.get('userFeedback').push(message);
    return state.set('userFeedback', userFeedback);
  
  } else {

    switch (action.type) {

      case 'REQUEST_START':
        var requestsPending = state.get('requestsPending');
        return state.set('requestsPending', requestsPending + 1);

      case 'REQUEST_DONE':
        var requestsPending = state.get('requestsPending');
        return state.set('requestsPending', requestsPending - 1);

      case 'DISMISS_MESSAGES':
        var userFeedback = state.get('userFeedback').clear();
        return state.merge({ userFeedback });
    }

  }
  return state;
}
import { Map, List } from 'immutable';
import { createMessage } from '../utils/messages';

const DEFAULT_STATE = Map({
  requestsPending: 0,
  userFeedback: List([])
});

const ERROR_MESSAGES = {
  POST_LOGIN_ERROR: "Unable to login.",
  POST_LOGOUT_ERROR: "Unable to logout.",
  POST_CHANGEPASSWORD_ERROR: "Unable to change password.",
  POST_REGISTER_ERROR: "Unable to register with provided credentials.",
  POST_UPDATEPROFILE_ERROR: "Unable to update profile.",
  GET_USERINFO_ERROR: "Unable to get user profile information from server.",
  POST_RESETPASSWORD_ERROR: "Unable to reset password.",
  POST_RESETCONFIRMPASSWORD_ERROR: "Unable to reset password.",
  GET_ACTIVATE_ERROR: "Unable to activate account."
}

const SUCCESS_MESSAGES = {
  POST_LOGIN_SUCCESS: "Successfully logged in.",
  POST_LOGOUT_SUCCESS: "Successfully logged out.",
  POST_CHANGEPASSWORD_SUCCESS: "Successfully changed password.",
  POST_REGISTER_SUCCESS: "Successfully registered. You can now log in.",
  POST_UPDATEPROFILE_SUCCESS: "Successfully updated profile information.",
  POST_RESETPASSWORD_SUCCESS: "Password successfully reset. You have recieved an email to confirm the reset.",
  POST_RESETCONFIRMPASSWORD_SUCCESS: "Password successfully reset.",
  GET_ACTIVATE_SUCCESS: "Account successfully activated."
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
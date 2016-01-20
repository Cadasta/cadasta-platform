
import { Map, List, fromJS } from 'immutable';

const DEFAULT_STATE = new Map({
  requestsPending: 0,
  userFeedback: new List([]),
});

const ERROR_MESSAGES = {
  LOGIN_ERROR: 'Unable to login with provided username and password.',
  LOGOUT_ERROR: 'Unable to logout.',
  CHANGEPASSWORD_ERROR: 'Unable to change password.',
  REGISTER_ERROR: 'Unable to register with provided credentials.',
  UPDATEPROFILE_ERROR: 'Unable to update profile.',
  USERINFO_ERROR: 'Unable to get user profile information from server.',
  RESETPASSWORD_ERROR: 'Unable to reset password.',
  RESETCONFIRMPASSWORD_ERROR: 'Unable to reset password.',
  ACTIVATE_ERROR: 'Unable to activate account.',
};

const SUCCESS_MESSAGES = {
  LOGIN_SUCCESS: 'Successfully logged in.',
  LOGOUT_SUCCESS: 'Successfully logged out.',
  CHANGEPASSWORD_SUCCESS: 'Successfully changed password.',
  REGISTER_SUCCESS: 'Successfully registered.',
  UPDATEPROFILE_SUCCESS: 'Successfully updated profile information.',
  RESETPASSWORD_SUCCESS: ('Password successfully reset. Check your inbox for ' +
                          'a link to confirm the reset.'),
  RESETCONFIRMPASSWORD_SUCCESS: 'Password successfully reset.',
  ACTIVATE_SUCCESS: 'Account successfully activated.',
};

function parseError(response) {
  let errorList = [];

  for (const key in response) {
    if (response.hasOwnProperty(key)) {
      errorList = errorList.concat(response[key]);
    }
  }

  return errorList;
}

function createMessage(type, msg, response) {
  const message = { type, msg };

  if (response) {
    if (response.network_error) {
      message.msg = response.network_error;
    } else {
      message.details = parseError(response);
    }
  }

  return fromJS(message);
}

export default function messages(state = DEFAULT_STATE, action) {
  let newState;
  let userFeedback = state.get('userFeedback');
  const requestsPending = state.get('requestsPending');

  if (action.type in SUCCESS_MESSAGES) {
    userFeedback = userFeedback.push(
      createMessage('success', SUCCESS_MESSAGES[action.type])
    );
    newState = state.set('userFeedback', userFeedback);
  } else if (action.type in ERROR_MESSAGES) {
    userFeedback = userFeedback.push(
      createMessage('error', ERROR_MESSAGES[action.type], action.response)
    );
    newState = state.set('userFeedback', userFeedback);
  } else {
    switch (action.type) {

      case 'REQUEST_START':
        newState = state.set('requestsPending', requestsPending + 1);
        break;

      case 'REQUEST_DONE':
        newState = state.set('requestsPending', requestsPending - 1);
        break;

      case 'DISMISS_MESSAGES':
        userFeedback = userFeedback.clear();
        newState = state.merge({ userFeedback });
        break;

      default:
        newState = state;
    }
  }

  return newState;
}

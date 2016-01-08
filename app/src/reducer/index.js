import { fromJS, Map, List } from 'immutable';
import { parseError } from '../utils/messages';

export const INITIAL_STATE = fromJS({
  user: {},
  messages: {
    requestsPending: 0,
    userFeedback: []
  },
  data: {}
});


export default function rootReducer(state = INITIAL_STATE, action) {
  switch (action.type) {

    case 'POST_LOGIN_SUCCESS':
      var user = state.get('user');

      user = user.merge( Map({ auth_token: action.response.auth_token }) );
      window.localStorage.setItem('auth_token', action.response.auth_token);

      return state.merge({ user });

    case 'POST_LOGIN_ERROR':
      var messages = state.get('messages');
      var userFeedback = messages.get('userFeedback').push(Map({
        type: 'error',
        msg: action.response.non_field_errors[0]
      }));
      messages = messages.set('userFeedback', userFeedback);

      return state.merge({ messages });

    case 'POST_LOGOUT_SUCCESS':
      window.localStorage.removeItem('auth_token');

      var user = state.get('user').delete('auth_token');
      return state.merge({ user });

    case 'POST_REGISTER_SUCCESS':
    case 'POST_UPDATEPROFILE_SUCCESS':
    case 'GET_USERINFO_SUCCESS':
      var user = state.get('user').merge(Map(action.response));
      var newState = state.merge({ user });

      return newState;

    case 'POST_CHANGEPASSWORD_ERROR':
      var message = Map({
        type: 'error',
        msg: "Unable to change password",
        details: fromJS(parseError(action.response))
      });

      var messages = state.get('messages')
      var userFeedback = messages.get('userFeedback').push(message);
      messages = messages.set('userFeedback', userFeedback);
      return state.merge({ messages });

    case 'POST_REGISTER_ERROR':
      var message = Map({
        type: 'error',
        msg: "Unable to register with provided credentials.",
        details: fromJS(parseError(action.response))
      });

      var messages = state.get('messages')
      var userFeedback = messages.get('userFeedback').push(message);
      messages = messages.set('userFeedback', userFeedback);
      return state.merge({ messages });

    case 'POST_UPDATEPROFILE_ERROR':
      var message = Map({
        type: 'error',
        msg: "Unable to update profile",
        details: fromJS(parseError(action.response))
      });

      var messages = state.get('messages')
      var userFeedback = messages.get('userFeedback').push(message);
      messages = messages.set('userFeedback', userFeedback);
      return state.merge({ messages });

    case 'REQUEST_START':
      var requestsPending = state.get('messages').get('requestsPending');
      var messages = state.get('messages').set('requestsPending', requestsPending + 1);
      return state.merge({messages});

    case 'REQUEST_DONE':
      var requestsPending = state.get('messages').get('requestsPending');
      var messages = state.get('messages').set('requestsPending', requestsPending - 1);
      return state.merge({messages});

    case 'DISMISS_MESSAGES':
      var messages = state.get('messages')
      var userFeedback = messages.get('userFeedback').clear();
      messages = messages.set('userFeedback', userFeedback);
      return state.merge({ messages });
  }

  return state;
}
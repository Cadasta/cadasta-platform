import { fromJS, Map, List } from 'immutable';

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

    case 'POST_LOGIN_DONE':
      var user = state.get('user');

      if (action.response.success) {

        user = user.merge( Map({ auth_token: action.response.content.auth_token }) );
        window.localStorage.setItem('auth_token', action.response.content.auth_token);

        return state.merge({ user });

      } else {

        var messages = state.get('messages');
        var userFeedback = messages.get('userFeedback').push(Map({
          type: 'error',
          msg: action.response.content.non_field_errors[0]
        }));
        messages = messages.set('userFeedback', userFeedback);

        return state.merge({ messages })

      }

      break;

    case 'POST_LOGOUT_DONE':
      if (action.response.success) {
        window.localStorage.removeItem('auth_token');

        var user = state.get('user').delete('auth_token');
        return state.merge({ user });
      }
      break;

    case 'POST_REGISTER_DONE':
    case 'POST_UPDATEPROFILE_DONE':
    case 'GET_USERINFO_DONE':
      if (action.response.success) {
        var user = state.get('user').merge(Map(action.response.content));
        var newState = state.merge({ user });

        return newState;  
      }
      break;

    case 'REQUEST_START':
      var requestsPending = state.get('messages').get('requestsPending');
      var messages = state.get('messages').set('requestsPending', requestsPending + 1);
      return state.merge({messages});

      break;

    case 'REQUEST_DONE':
      var requestsPending = state.get('messages').get('requestsPending');
      var messages = state.get('messages').set('requestsPending', requestsPending - 1);
      return state.merge({messages});

      break;
  }

  return state;
}
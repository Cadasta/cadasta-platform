import { Map, List } from 'immutable';

export const INITIAL_STATE = Map({
  user: Map(),
  messages: List([]),
  data: Map()
});


export default function rootReducer(state = INITIAL_STATE, action) {
  switch (action.type) {

    case 'POST_LOGIN_DONE':
      var user = state.get('user');
      if (action.response.auth_token) {
        user = user.merge( Map({ auth_token: action.response.auth_token }) );
        window.localStorage.setItem('auth_token', action.response.auth_token);

        return state.merge({ user });
      }

    case 'POST_LOGOUT_DONE':
      window.localStorage.removeItem('auth_token');

      var user = state.get('user').delete('auth_token');
      return state.merge({ user });

    case 'MESSAGE_DISMISS':
      let messages = state.get('messages').filter(obj => obj.get('id') !== action.messageId);

      return state.merge({
        messages
      });
  }

  return state;
}
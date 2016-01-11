import { Map, List } from 'immutable';

const defaultState = Map({});

export default function user(state = defaultState, action) {
  switch (action.type) {

  	case 'POST_LOGIN_SUCCESS':
      window.localStorage.setItem('auth_token', action.response.auth_token);

      return state.merge({ auth_token: action.response.auth_token });

    case 'POST_LOGOUT_SUCCESS':
      window.localStorage.removeItem('auth_token');
      return Map({});

    case 'POST_REGISTER_SUCCESS':
    case 'POST_UPDATEPROFILE_SUCCESS':
    case 'GET_USERINFO_SUCCESS':
      return state.merge( action.response );
    
    default:
      return state
  }
}
import { Map, List } from 'immutable';

const defaultState = Map({});

export default function user(state = defaultState, action) {
  switch (action.type) {

  	case 'LOGIN_SUCCESS':
      window.localStorage.setItem('auth_token', action.response.auth_token);

      return state.merge({ auth_token: action.response.auth_token });

    case 'LOGOUT_SUCCESS':
      window.localStorage.removeItem('auth_token');
      return Map({});

    case 'REGISTER_SUCCESS':
    case 'UPDATEPROFILE_SUCCESS':
    case 'USERINFO_SUCCESS':
      return state.merge( action.response );
    
    default:
      return state
  }
}
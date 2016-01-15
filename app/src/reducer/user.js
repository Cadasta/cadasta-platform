import { Map, List } from 'immutable';

const defaultState = Map({});

function setToken(token, rememberMe) {
  window.sessionStorage.setItem('auth_token', token);

  if (rememberMe) {
    window.localStorage.setItem('auth_token', token);  
  }
}

export default function user(state = defaultState, action) {
  switch (action.type) {

  	case 'LOGIN_SUCCESS':
      setToken(action.response.auth_token, action.rememberMe);

      return state.merge({ auth_token: action.response.auth_token });

    case 'LOGOUT_SUCCESS':
      window.localStorage.removeItem('auth_token');
      window.sessionStorage.removeItem('auth_token');
      return Map({});

    case 'REGISTER_SUCCESS':
      setToken(action.response.auth_token);
      return state.merge( action.response );

    case 'UPDATEPROFILE_SUCCESS':
    case 'USERINFO_SUCCESS':
      return state.merge( action.response );
    
    default:
      return state
  }
}
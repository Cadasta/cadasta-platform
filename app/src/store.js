import { createStore, applyMiddleware } from 'redux';
import thunk from 'redux-thunk';
import rootReducer from './reducer';

import history from './history';

import { ROUTER_REDIRECT } from './actions/router';


const redirect = store => next => action => {
  if (action.type === 'ROUTER_REDIRECT') {
    history.replaceState(null, action.redirectTo);  
  }

  return next(action);
}


let store;

if (!store) {
  let createStoreWithMiddleware = applyMiddleware(redirect, thunk)(createStore);
  store = createStoreWithMiddleware(rootReducer);
}

export default store;

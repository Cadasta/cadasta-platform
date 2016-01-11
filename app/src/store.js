import { createStore, applyMiddleware } from 'redux';
import thunk from 'redux-thunk';
import reducer from './reducer';

import history from './history';

import { ROUTER_REDIRECT } from './actions/router';
import { dismissMessages } from './actions/messages';


const messages = store => next => action => {
  if (action.type && (action.type.endsWith('_SUCCESS') || action.type.endsWith('_ERROR'))) {
    store.dispatch(dismissMessages());
  }

  return next(action);
}


const redirect = store => next => action => {
  if (action.type === ROUTER_REDIRECT) {
    history.replaceState(null, action.redirectTo);  
  }

  return next(action);
}


let store;

if (!store) {
  let createStoreWithMiddleware = applyMiddleware(messages, redirect, thunk)(createStore);
  store = createStoreWithMiddleware(reducer);
}

export default store;

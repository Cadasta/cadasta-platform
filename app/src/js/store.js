import createStore from 'redux/lib/createStore';
import applyMiddleware from 'redux/lib/applyMiddleware';
import thunk from 'redux-thunk';
import reducer from './reducer';

import history from './history';

import { ROUTER_REDIRECT } from './core/actions';
import { dismissMessages } from './messages/actions';


const messages = store => next => action => {
  if (action.type && !action.keepMessages) {
    store.dispatch(dismissMessages());
  }

  return next(action);
};


const redirect = () => next => action => {
  if (action.type === ROUTER_REDIRECT) {
    history.replaceState(null, action.redirectTo);
  }

  return next(action);
};


let store;

if (!store) {
  const createStoreWithMiddleware = applyMiddleware(messages, redirect, thunk)(createStore);
  store = createStoreWithMiddleware(reducer);
}

export default store;

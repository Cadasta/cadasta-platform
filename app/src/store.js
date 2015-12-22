import { createStore, applyMiddleware } from 'redux';
import thunk from 'redux-thunk';
import rootReducer from './reducer';


export default function makeStore() {
  let createStoreWithMiddleware = applyMiddleware(thunk)(createStore);

  return createStoreWithMiddleware(rootReducer);
}

import { createStore, applyMiddleware } from 'redux';
import thunk from 'redux-thunk';
import rootReducer from './reducer';


let store;

if (!store) {
  let createStoreWithMiddleware = applyMiddleware(thunk)(createStore);
  store = createStoreWithMiddleware(rootReducer);
}

export default store;

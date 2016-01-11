import { fromJS } from 'immutable';

import { combineReducers } from 'redux';
import user from './user';
import messages from './messages';
import data from './data';

const reducer = combineReducers({
  user,
  messages,
  data
});

export default reducer;

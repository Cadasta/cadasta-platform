import { Map, List } from 'immutable';
import { createMessage } from '../utils/messages';

const defaultState = Map({
  requestsPending: 0,
  userFeedback: List([])
});

export default function messages(state = defaultState, action) {
  switch (action.type) {

    case 'POST_LOGIN_ERROR':
      var message = createMessage('error', "Unable to login.", action.response)
      var userFeedback = state.get('userFeedback').push(message);
      return state.set('userFeedback', userFeedback);

    case 'POST_CHANGEPASSWORD_ERROR':
      var message = createMessage('error', "Unable to change password", action.response)

      var userFeedback = state.get('userFeedback').push(message);
      return state.set('userFeedback', userFeedback);

    case 'POST_REGISTER_ERROR':
      var message = createMessage('error', "Unable to register with provided credentials.", action.response)

      var userFeedback = state.get('userFeedback').push(message);
      return state.set('userFeedback', userFeedback);

    case 'POST_UPDATEPROFILE_ERROR':
      var message = createMessage('error', "Unable to update profile", action.response)

      var userFeedback = state.get('userFeedback').push(message);
      return state.set('userFeedback', userFeedback);

    case 'REQUEST_START':
      var requestsPending = state.get('requestsPending');
      return state.set('requestsPending', requestsPending + 1);

    case 'REQUEST_DONE':
      var requestsPending = state.get('requestsPending');
      return state.set('requestsPending', requestsPending - 1);

    case 'DISMISS_MESSAGES':
      var userFeedback = state.get('userFeedback').clear();
      return state.merge({ userFeedback });
    
    default:
      return state
  }
}
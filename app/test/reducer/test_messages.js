import { Map, List, fromJS } from 'immutable';
import {expect} from 'chai';

import rootReducer from '../../src/reducer'

describe('reducer', () => {
  it('handles REQUEST_START', () => {
    const state = fromJS({
      messages: {
        requestsPending: 0    
      }
    });

    const action = {
      type: 'REQUEST_START'
    };

    const nextState = rootReducer(state, action);
    const requestsPending = nextState.get('messages').get('requestsPending');

    expect(requestsPending).to.equal(1);
  });

  it('handles REQUEST_DONE', () => {
    const state = fromJS({
      messages: {
        requestsPending: 1
      }
    });

    const action = {
      type: 'REQUEST_DONE'
    };

    const nextState = rootReducer(state, action);
    const requestsPending = nextState.get('messages').get('requestsPending');

    expect(requestsPending).to.equal(0);
  });

  it('handles DISMISS_MESSAGES', () => {
    const state = fromJS({
      messages: {
        requestsPending: 0,
        userFeedback: [
          "Test Message"
        ]
      }
    });

    const action = {
      type: 'DISMISS_MESSAGES'
    };

    const nextState = rootReducer(state, action);
    const requestsPending = nextState.get('messages').get('userFeedback').count();

    expect(requestsPending).to.equal(0);
  });
});
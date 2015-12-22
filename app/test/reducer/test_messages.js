import { Map, List, fromJS } from 'immutable';
import {expect} from 'chai';

import rootReducer from '../../src/reducer'

describe('reducer', () => {
  it('handles MESSAGE_DISMISS', () => {
    const state = fromJS({
      messages: [
          {
            type: 'loading',
            msg: "Test message",
            id: 1
          }, {
            type: 'success',
            msg: "Well done",
            id: 2
          }
        ]
    });

    const action = {
          type: 'MESSAGE_DISMISS',
          messageId: 1
        };

    const nextState = rootReducer(state, action);
    const messages = nextState.get('messages');

    expect(messages.count()).to.equal(1);
    expect(messages.first().get('id')).to.equal(2);
  });
});
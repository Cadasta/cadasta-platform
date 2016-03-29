import { fromJS } from 'immutable';
import { expect } from 'chai';

import store from '../src/js/store';

describe('store', () => {
  it('is a Redux store configured with the correct reducer', () => {
    expect(store.getState()).to.deep.equal({
      user: fromJS({ }),
      messages: fromJS({
        requestsPending: 0,
        userFeedback: [],
      }),
    });

    store.dispatch({ type: 'REQUEST_START' });

    const state = store.getState();
    expect(state).to.have.property('user');
    expect(state.messages.get('requestsPending')).to.equal(1);
  });
});

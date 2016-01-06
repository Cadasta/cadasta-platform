import {Map, fromJS} from 'immutable';
import {expect} from 'chai';

import store from '../../src/store';
import { INITIAL_STATE } from '../../src/reducer'

describe('store', () => {

  it('is a Redux store configured with the correct reducer', () => {
    expect(store.getState()).to.equal(INITIAL_STATE);

    store.dispatch({
      type: 'REQUEST_START'
    });

    expect(store.getState()).to.equal(fromJS({
      user: {},
      messages: {
        requestsPending: 1,
        userFeedback: []
      },
      data: {}
    }));
  });

});
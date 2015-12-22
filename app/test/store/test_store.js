import {Map, fromJS} from 'immutable';
import {expect} from 'chai';

import makeStore from '../../src/store';
import { INITIAL_STATE } from '../../src/reducer'

describe('store', () => {

  it('is a Redux store configured with the correct reducer', () => {
    const store = makeStore();
    expect(store.getState()).to.equal(INITIAL_STATE);

    store.dispatch({
      type: 'POST_LOGIN_DONE',
      response: {
        auth_token: "mskdj8sdh8shadhs"
      }
    });

    expect(store.getState()).to.equal(fromJS({
      user: {
        auth_token: "mskdj8sdh8shadhs"
      },
      messages: [],
      data: {}
    }));
  });

});
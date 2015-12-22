import { Map, List, fromJS } from 'immutable';
import {expect} from 'chai';

import Storage from '../utils/Storage';

import rootReducer from '../../src/reducer'

describe('reducer', () => {
  beforeEach(() => {
    window.localStorage = new Storage();
  });

  it('handles POST_LOGIN_DONE', () => {
    const state = Map({
      user: Map()
    });

    const action = {
      type: 'POST_LOGIN_DONE',
      response: {
        auth_token: "mskdj8sdh8shadhs"
      }
    };
    const nextState = rootReducer(state, action);

    expect(nextState).to.equal(fromJS({
      user: {
        auth_token: "mskdj8sdh8shadhs"
      }
    }));

    expect(window.localStorage.getItem('auth_token')).to.equal("mskdj8sdh8shadhs");
  });

  it('handles POST_LOGOUT_DONE', () => {
    const state = fromJS({
      user: {
        auth_token: "mskdj8sdh8shadhs"
      }
    });

    const action = {
      type: 'POST_LOGOUT_DONE',
      response: { }
    };
    const nextState = rootReducer(state, action);

    expect(nextState).to.equal(fromJS({
      user: {}
    }));

    expect(window.localStorage.getItem('auth_token')).to.be.null;
  });
});

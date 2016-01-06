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
        success: true,
        content: {
          auth_token: "mskdj8sdh8shadhs"  
        }
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
      response: {
        success: true,
        content: { }
      }
    };
    const nextState = rootReducer(state, action);

    expect(nextState).to.equal(fromJS({
      user: {}
    }));

    expect(window.localStorage.getItem('auth_token')).to.be.null;
  });

  it('handles POST_REGISTER_DONE', () => {
    const state = fromJS({ user: { } });

    const action = {
      type: 'POST_REGISTER_DONE',
      response: {
        success: true,
        content: {
          email: "john@beatles.uk",
          email_verified: false,
          first_name: "John",
          last_name: "Lennon",
          username: "john"
        }
      }
    };
    const nextState = rootReducer(state, action);

    expect(nextState).to.equal(fromJS({
      user: {
        email: "john@beatles.uk",
        email_verified: false,
        first_name: "John",
        last_name: "Lennon",
        username: "john"
      }
    }));
  });

  it('handles POST_UPDATEPROFILE_DONE', () => {
    const state = fromJS({ user: {
      email: "john@beatles.uk",
        first_name: "John",
        last_name: "Lennon",
        username: "john"
      }});

    const action = {
      type: 'POST_UPDATEPROFILE_DONE',
      response: {
        success: true,
        content: {
          email: "paul@beatles.uk",
          first_name: "paul",
          last_name: "McCartney",
          username: "Paul"
        }
      }
    };
    const nextState = rootReducer(state, action);

    expect(nextState).to.equal(fromJS({
      user: {
        email: "paul@beatles.uk",
        first_name: "paul",
        last_name: "McCartney",
        username: "Paul"
      }
    }));
  });

  it('handles GET_USERINFO_DONE', () => {
    const state = fromJS({ user: {} });

    const action = {
      type: 'GET_USERINFO_DONE',
      response: {
        success: true,
        content: {
          email: "paul@beatles.uk",
          first_name: "paul",
          last_name: "McCartney",
          username: "Paul"
        }
      }
    };
    const nextState = rootReducer(state, action);

    expect(nextState).to.equal(fromJS({
      user: {
        email: "paul@beatles.uk",
        first_name: "paul",
        last_name: "McCartney",
        username: "Paul"
      }
    }));
  });
});

import { Map, List, fromJS } from 'immutable';
import {expect} from 'chai';

import Storage from '../utils/Storage';

import rootReducer from '../../src/reducer'

describe('reducer', () => {
  beforeEach(() => {
    window.localStorage = new Storage();
  });

  it('handles POST_LOGIN_SUCCESS with successful login', () => {
    const state = Map({
      user: Map()
    });

    const action = {
      type: 'POST_LOGIN_SUCCESS',
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

  it('handles POST_LOGIN_ERROR', () => {
    const state = Map({
      user: Map(),
      messages: Map({
        userFeedback: List([])
      })
    });

    const action = {
      type: 'POST_LOGIN_ERROR',
      response: {
        "non_field_errors": ["Unable to login with provided credentials."]
      }
    };
    const nextState = rootReducer(state, action);

    expect(nextState).to.equal(fromJS({
      user: { },
      messages: {
        userFeedback: [{
          type: 'error',
          msg: "Unable to login with provided credentials."
        }]
      }
    }));
  });

  it('handles POST_LOGOUT_SUCCESS', () => {
    const state = fromJS({
      user: {
        auth_token: "mskdj8sdh8shadhs"
      }
    });

    const action = {
      type: 'POST_LOGOUT_SUCCESS'
    };
    const nextState = rootReducer(state, action);

    expect(nextState).to.equal(fromJS({
      user: {}
    }));

    expect(window.localStorage.getItem('auth_token')).to.be.null;
  });

  it('handles POST_REGISTER_SUCCESS', () => {
    const state = fromJS({ user: { } });

    const action = {
      type: 'POST_REGISTER_SUCCESS',
      response: {
        email: "john@beatles.uk",
        email_verified: false,
        first_name: "John",
        last_name: "Lennon",
        username: "john"
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

  it('handles POST_UPDATEPROFILE_SUCCESS', () => {
    const state = fromJS({ user: {
      email: "john@beatles.uk",
        first_name: "John",
        last_name: "Lennon",
        username: "john"
      }});

    const action = {
      type: 'POST_UPDATEPROFILE_SUCCESS',
      response: {
        email: "paul@beatles.uk",
        first_name: "paul",
        last_name: "McCartney",
        username: "Paul"
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

  it('handles GET_USERINFO_SUCCESS', () => {
    const state = fromJS({ user: {} });

    const action = {
      type: 'GET_USERINFO_SUCCESS',
      response: {
        email: "paul@beatles.uk",
        first_name: "paul",
        last_name: "McCartney",
        username: "Paul"
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

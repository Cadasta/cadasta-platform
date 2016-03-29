import { fromJS } from 'immutable';
import { expect } from 'chai';

import user from '../../src/js/account/reducer';
import Storage from '../test-helper/Storage';

describe('user reducer', () => {
  beforeEach(() => {
    window.localStorage = new Storage();
    window.sessionStorage = new Storage();
  });

  it('handles LOGIN_SUCCESS', () => {
    const state = fromJS({ });

    const action = {
      type: 'LOGIN_SUCCESS',
      response: {
        auth_token: 'mskdj8sdh8shadhs',
      },
      rememberMe: false,
    };
    const nextState = user(state, action);

    expect(nextState).to.deep.equal(fromJS({
      auth_token: 'mskdj8sdh8shadhs',
    }));

    expect(window.localStorage.getItem('auth_token')).to.be.null;
    expect(window.sessionStorage.getItem('auth_token')).to.equal('mskdj8sdh8shadhs');
  });

  it('handles LOGIN_SUCCESS with remember me', () => {
    const state = fromJS({ });

    const action = {
      type: 'LOGIN_SUCCESS',
      response: {
        auth_token: 'mskdj8sdh8shadhs',
      },
      rememberMe: true,
    };
    const nextState = user(state, action);

    expect(nextState).to.deep.equal(fromJS({
      auth_token: 'mskdj8sdh8shadhs',
    }));

    expect(window.localStorage.getItem('auth_token')).to.equal('mskdj8sdh8shadhs');
    expect(window.sessionStorage.getItem('auth_token')).to.equal('mskdj8sdh8shadhs');
  });

  it('handles LOGOUT_SUCCESS', () => {
    window.sessionStorage.setItem('auth_token', 'mskdj8sdh8shadhs');
    window.localStorage.setItem('auth_token', 'mskdj8sdh8shadhs');

    const state = fromJS({ auth_token: 'mskdj8sdh8shadhs' });
    const action = { type: 'LOGOUT_SUCCESS' };
    const nextState = user(state, action);

    expect(nextState).to.equal(fromJS({ }));

    expect(window.localStorage.getItem('auth_token')).to.be.null;
    expect(window.sessionStorage.getItem('auth_token')).to.be.null;
  });

  it('handles LOGOUT_SUCCESS', () => {
    window.sessionStorage.setItem('auth_token', 'mskdj8sdh8shadhs');

    const state = fromJS({ auth_token: 'mskdj8sdh8shadhs' });
    const action = { type: 'LOGOUT_SUCCESS' };
    const nextState = user(state, action);

    expect(nextState).to.equal(fromJS({ }));

    expect(window.localStorage.getItem('auth_token')).to.be.null;
    expect(window.sessionStorage.getItem('auth_token')).to.be.null;
  });

  it('handles REGISTER_SUCCESS', () => {
    const state = fromJS({ });

    const action = {
      type: 'REGISTER_SUCCESS',
      response: {
        email: 'john@beatles.uk',
        email_verified: false,
        first_name: 'John',
        last_name: 'Lennon',
        username: 'john',
      },
    };
    const nextState = user(state, action);

    expect(nextState).to.deep.equal(fromJS({
      email: 'john@beatles.uk',
      email_verified: false,
      first_name: 'John',
      last_name: 'Lennon',
      username: 'john',
    }));
  });

  it('handles UPDATEPROFILE_SUCCESS', () => {
    const state = fromJS({
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
      username: 'john',
    });

    const action = {
      type: 'UPDATEPROFILE_SUCCESS',
      response: {
        email: 'paul@beatles.uk',
        first_name: 'paul',
        last_name: 'McCartney',
        username: 'Paul',
      },
    };
    const nextState = user(state, action);

    expect(nextState).to.deep.equal(fromJS({
      email: 'paul@beatles.uk',
      first_name: 'paul',
      last_name: 'McCartney',
      username: 'Paul',
    }));
  });

  it('handles USERINFO_SUCCESS', () => {
    const state = fromJS({ });

    const action = {
      type: 'USERINFO_SUCCESS',
      response: {
        email: 'paul@beatles.uk',
        first_name: 'paul',
        last_name: 'McCartney',
        username: 'Paul',
      },
    };
    const nextState = user(state, action);

    expect(nextState).to.deep.equal(fromJS({
      email: 'paul@beatles.uk',
      first_name: 'paul',
      last_name: 'McCartney',
      username: 'Paul',
    }));
  });
});

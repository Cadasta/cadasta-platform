import {expect} from 'chai';
import nock from 'nock';
import { applyMiddleware } from 'redux'
import configureMockStore from 'redux-mock-store'
import thunk from 'redux-thunk'

import Storage from '../utils/Storage';

import SETTINGS from '../../src/settings';
import history from '../../src/history';
import * as accountActions from '../../src/actions/account';


const middlewares = [ thunk ]
const mockStore = configureMockStore(middlewares)

describe('Actions: account', () => {
  it ('creates POST_LOGIN_START', () => {
    const action = accountActions.postLoginStart();

    expect(action).to.deep.equal({
      type: accountActions.POST_LOGIN_START
    })
  });

  it ('creates POST_LOGIN_DONE', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk'
    }
    const action = accountActions.postLoginDone(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_LOGIN_DONE,
      response
    })
  });

  it ('creates POST_LOGIN_DONE when login was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      password: '123455'
    }
    
    const response = { 
        username: 'John',
        email: 'john@beatles.uk',
        first_name: 'John',
        last_name: 'Lennon',
        token: '8qwihd8zds87hds78'
      };

    nock(SETTINGS.API_BASE)
      .post('/account/login/', userCredentials)
      .reply(200, response)

    const expectedActions = [
      { type: accountActions.POST_LOGIN_START },
      { type: accountActions.POST_LOGIN_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogin(userCredentials))
  });

  it ('creates POST_LOGOUT_START', () => {
    const action = accountActions.postLogoutStart();

    expect(action).to.deep.equal({
      type: accountActions.POST_LOGOUT_START
    })
  });

  it ('creates POST_LOGOUT_DONE', () => {
    const response = {}
    const action = accountActions.postLogoutDone(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_LOGOUT_DONE,
      response
    })
  });

  it ('creates POST_LOGOUT_DONE when logout was succesful', (done) => {
    window.localStorage = new Storage();
    window.localStorage.setItem('auth_token', '8937hds8yh8hsd')

    const response = { };

    nock(SETTINGS.API_BASE)
      .post('/account/logout/', {})
      .reply(200, response)

    const expectedActions = [
      { type: accountActions.POST_LOGOUT_START },
      { type: accountActions.POST_LOGOUT_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogout({}))
  });

  it ('creates POST_REGISTER_START', () => {
    const action = accountActions.postRegisterStart();

    expect(action).to.deep.equal({
      type: accountActions.POST_REGISTER_START
    })
  });

  it ('creates POST_REGISTER_DONE', () => {
    const response = {}
    const action = accountActions.postRegisterDone(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_REGISTER_DONE,
      response
    })
  });

  it ('creates POST_REGISTER_DONE when registration was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
      password: '123456',
      password_repeat: '123456',
    }
    
    const response = { 
        username: 'John',
        email: 'john@beatles.uk',
        first_name: 'John',
        last_name: 'Lennon',
      };

    nock(SETTINGS.API_BASE)
      .post('/account/register/', userCredentials)
      .reply(201, response)

    const expectedActions = [
      { type: accountActions.POST_REGISTER_START },
      { type: accountActions.POST_REGISTER_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountRegister(userCredentials))

    done();
  });
});
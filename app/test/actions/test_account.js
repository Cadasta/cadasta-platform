import {expect} from 'chai';
import nock from 'nock';
import { applyMiddleware } from 'redux'
import configureMockStore from 'redux-mock-store'
import thunk from 'redux-thunk'

import SETTINGS from '../../src/settings';
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
});
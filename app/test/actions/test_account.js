import {expect} from 'chai';
import nock from 'nock';
import configureMockStore from 'redux-mock-store'
import thunk from 'redux-thunk'

import Storage from '../utils/Storage';

import SETTINGS from '../../src/settings';
import * as accountActions from '../../src/actions/account';
import * as messageActions from '../../src/actions/messages';
import * as routerActions from '../../src/actions/router';

var middlewares = [ thunk ];
var mockStore = configureMockStore(middlewares);

describe('Actions: account', () => {
  beforeEach(() => {
    window.localStorage = new Storage();
    window.localStorage.setItem('auth_token', 's8yc8shch98s');
  });

  /* ********************************************************
   *
   * Login
   *
   * ********************************************************/

  it ('creates POST_LOGIN_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk'
    }
    const action = accountActions.postLoginSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_LOGIN_SUCCESS,
      response
    })
  });

  it ('creates POST_LOGIN_SUCCESS when login was succesful', (done) => {
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

    nock(SETTINGS.API_BASE)
      .get('/account/me/')
      .reply(200, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_LOGIN_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE },
      { type: routerActions.ROUTER_REDIRECT, redirectTo: '/dashboard/' },
      { type: messageActions.REQUEST_START },
      { type: accountActions.GET_USERINFO_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogin(userCredentials))
  });

  it ('creates POST_LOGIN_ERROR', () => {
    const response = {
      "non_field_errors": ["Unable to login with provided credentials."]
    }
    const action = accountActions.postLoginError(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_LOGIN_ERROR,
      response
    })
  });

  it ('creates POST_LOGIN_ERROR when login was unsuccesful', (done) => {
    const userCredentials = {
      username: 'John',
      password: '123455'
    }
    
    const response = {
      "non_field_errors": ["Unable to login with provided credentials."]
    }

    nock(SETTINGS.API_BASE)
      .post('/account/login/', userCredentials)
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_LOGIN_ERROR, response: response },
      { type: messageActions.REQUEST_DONE },
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogin(userCredentials))
  });


  /* ********************************************************
   *
   * Logout
   *
   * ********************************************************/

  it ('creates POST_LOGOUT_SUCCESS', () => {
    const action = accountActions.postLogoutSuccess();

    expect(action).to.deep.equal({
      type: accountActions.POST_LOGOUT_SUCCESS
    })
  });

  it ('creates POST_LOGOUT_SUCCESS when logout was succesful', (done) => {
    window.localStorage = new Storage();
    window.localStorage.setItem('auth_token', '8937hds8yh8hsd')

    nock(SETTINGS.API_BASE)
      .post('/account/logout/', {})
      .reply(200)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_LOGOUT_SUCCESS },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogout({}))
  });


  /* ********************************************************
   *
   * Register
   *
   * ********************************************************/

  it ('creates POST_REGISTER_SUCCESS', () => {
    const response = {}
    const action = accountActions.postRegisterSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_REGISTER_SUCCESS,
      response
    })
  });

  it ('creates POST_REGISTER_SUCCESS when registration was succesful', (done) => {
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
      last_name: 'Lennon'
    };

    nock(SETTINGS.API_BASE)
      .post('/account/register/', userCredentials)
      .reply(201, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_REGISTER_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE },
      { type: routerActions.ROUTER_REDIRECT, redirectTo: '/account/login/' }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountRegister(userCredentials))
  });

  it ('creates POST_REGISTER_ERROR', () => {
    const response = {
      "email": ["Another user is already registered with this email address"]
    }
    const action = accountActions.postRegisterError(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_REGISTER_ERROR,
      response
    })
  });

  it ('creates POST_REGISTER_ERROR when registration was not succesful', (done) => {
    const userCredentials = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
      password: '123456',
      password_repeat: '123456',
    }
    
    const response = {
      "email": ["Another user is already registered with this email address"]
    }

    nock(SETTINGS.API_BASE)
      .post('/account/register/', userCredentials)
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_REGISTER_ERROR, response: response },
      { type: messageActions.REQUEST_DONE },
      { type: routerActions.ROUTER_REDIRECT, redirectTo: '/account/register/' }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountRegister(userCredentials))
  });


  /* ********************************************************
   *
   * Get user info
   *
   * ********************************************************/

  it ('creates GET_USERINFO_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    }
    const action = accountActions.getUserInfoSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.GET_USERINFO_SUCCESS,
      response
    })
  });

  it ('creates GET_USERINFO_SUCCESS when profile update was succesful', (done) => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    };

    nock(SETTINGS.API_BASE)
      .get('/account/me/')
      .reply(200, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.GET_USERINFO_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountGetUserInfo());
  });


  /********************************************************
   *
   * Update profile
   *
   * *******************************************************/

  it ('creates POST_UPDATEPROFILE_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    }
    const action = accountActions.postUpdateProfileSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_UPDATEPROFILE_SUCCESS,
      response
    })
  });

  it ('creates POST_UPDATEPROFILE_SUCCESS when profile update was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    }
    
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    };

    nock(SETTINGS.API_BASE)
      .put('/account/me/', userCredentials)
      .reply(200, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_UPDATEPROFILE_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountUpdateProfile(userCredentials));
  });


  /* ********************************************************
   *
   * Change password
   *
   * ********************************************************/

  it ('creates POST_CHANGEPASSWORD_SUCCESS', () => {
    const action = accountActions.postChangePasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.POST_CHANGEPASSWORD_SUCCESS
    })
  });

  it ('creates POST_CHANGEPASSWORD_SUCCESS when profile update was succesful', (done) => {
    const passwords = {
      new_password: "123456",
      re_new_password: "123456",
      current_password: "78910"
    }

    nock(SETTINGS.API_BASE)
      .post('/account/password/', passwords)
      .reply(200)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_CHANGEPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountChangePassword(passwords));
  });

  /* ********************************************************
   *
   * Reset password
   *
   * ********************************************************/

  it ('creates POST_RESETPASSWORD_SUCCESS', () => {
    const action = accountActions.postResetPasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.POST_RESETPASSWORD_SUCCESS
    })
  });

  it ('creates POST_RESETPASSWORD_SUCCESS when password change was succesful', (done) => {
    const user = {
      email: 'john@beatles.uk'
    }

    nock(SETTINGS.API_BASE)
      .post('/account/password/reset/', user)
      .reply(200)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_RESETPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetPassword(user));
  });

  /* ********************************************************
   *
   * Confirm reset password
   *
   * ********************************************************/

  it ('creates POST_RESETCONFIRMPASSWORD_SUCCESS', () => {
    const action = accountActions.postResetConfirmPasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.POST_RESETCONFIRMPASSWORD_SUCCESS
    })
  });

  it ('creates POST_RESETCONFIRMPASSWORD_SUCCESS when password reset was succesful', (done) => {
    const user = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
      new_password: '123456',
      re_new_password: '123456'
    }

    nock(SETTINGS.API_BASE)
      .post('/account/password/reset/confirm/', user)
      .reply(200)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_RESETCONFIRMPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetConfirmPassword(user));
  });

  /* ********************************************************
   *
   * Activate account
   *
   * ********************************************************/

  it ('creates POST_ACTIVATE_SUCCESS', () => {
    const action = accountActions.postActivateSuccess();

    expect(action).to.deep.equal({
      type: accountActions.POST_ACTIVATE_SUCCESS
    })
  });

  it ('creates POST_ACTIVATE_SUCCESS when account activation was succesful', (done) => {
    const data = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
    }

    nock(SETTINGS.API_BASE)
      .post('/account/activate/', data)
      .reply(200)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.POST_ACTIVATE_SUCCESS },
      { type: messageActions.REQUEST_DONE },
      { type: routerActions.ROUTER_REDIRECT, redirectTo: '/account/login/' }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountActivate(data));
  });
});

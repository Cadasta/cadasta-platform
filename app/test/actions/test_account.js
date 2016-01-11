import {expect} from 'chai';
import nock from 'nock';
import configureMockStore from 'redux-mock-store'
import thunk from 'redux-thunk'

import Storage from '../test-helper/Storage';

import SETTINGS from '../../src/settings';
import * as accountActions from '../../src/actions/account';
import * as messageActions from '../../src/actions/messages';
import * as routerActions from '../../src/actions/router';

var middlewares = [ thunk ];
var mockStore = configureMockStore(middlewares);

describe('Actions: account', () => {
  beforeEach(() => {
    window.sessionStorage = new Storage();
    window.sessionStorage.setItem('auth_token', 's8yc8shch98s');
  });

  /* ********************************************************
   *
   * Login
   *
   * ********************************************************/

  it ('creates LOGIN_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
    }
    const action = accountActions.postLoginSuccess(response, true);

    expect(action).to.deep.equal({
      type: accountActions.LOGIN_SUCCESS,
      response,
      rememberMe: true
    })
  });

  it ('creates LOGIN_SUCCESS when login was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      password: '123455',
      rememberMe: true
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
      .get('/account/')
      .reply(200, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.LOGIN_SUCCESS, response, rememberMe: true },
      { type: messageActions.REQUEST_DONE },
      { type: routerActions.ROUTER_REDIRECT, redirectTo: '/dashboard/' },
      { type: messageActions.REQUEST_START },
      { type: accountActions.USERINFO_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogin(userCredentials))
  });

  it ('creates LOGIN_ERROR', () => {
    const response = {
      "non_field_errors": ["Unable to login with provided credentials."]
    }
    const action = accountActions.postLoginError(response);

    expect(action).to.deep.equal({
      type: accountActions.LOGIN_ERROR,
      response
    })
  });

  it ('creates LOGIN_ERROR when login was unsuccesful', (done) => {
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
      { type: accountActions.LOGIN_ERROR, response: response },
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

  it ('creates LOGOUT_SUCCESS', () => {
    const action = accountActions.postLogoutSuccess();

    expect(action).to.deep.equal({
      type: accountActions.LOGOUT_SUCCESS
    })
  });

  it ('creates LOGOUT_SUCCESS when logout was succesful', (done) => {
    window.localStorage = new Storage();
    window.localStorage.setItem('auth_token', '8937hds8yh8hsd')

    nock(SETTINGS.API_BASE)
      .post('/account/logout/', {})
      .reply(200)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.LOGOUT_SUCCESS },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogout({}))
  });

  it ('creates LOGOUT_ERROR', () => {
    const response = { some: "error" }
    const action = accountActions.postLogoutError(response);

    expect(action).to.deep.equal({
      type: 'LOGOUT_ERROR',
      response
    })
  });

  it ('creates LOGOUT_ERROR when logout was not succesful', (done) => {
    const response = { some: "error" }

    nock(SETTINGS.API_BASE)
      .post('/account/logout/', {})
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.LOGOUT_ERROR, response },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogout())
  });


  /* ********************************************************
   *
   * Register
   *
   * ********************************************************/

  it ('creates REGISTER_SUCCESS', () => {
    const response = {}
    const action = accountActions.postRegisterSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.REGISTER_SUCCESS,
      response
    })
  });

  it ('creates REGISTER_SUCCESS when registration was succesful', (done) => {
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
      { type: accountActions.REGISTER_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE },
      { type: routerActions.ROUTER_REDIRECT, redirectTo: '/account/login/' }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountRegister(userCredentials))
  });

  it ('creates REGISTER_ERROR', () => {
    const response = {
      "email": ["Another user is already registered with this email address"]
    }
    const action = accountActions.postRegisterError(response);

    expect(action).to.deep.equal({
      type: accountActions.REGISTER_ERROR,
      response
    })
  });

  it ('creates REGISTER_ERROR when registration was not succesful', (done) => {
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
      { type: accountActions.REGISTER_ERROR, response: response },
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

  it ('creates USERINFO_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    }
    const action = accountActions.getUserInfoSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.USERINFO_SUCCESS,
      response
    })
  });

  it ('creates USERINFO_SUCCESS when profile update was succesful', (done) => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    };

    nock(SETTINGS.API_BASE)
      .get('/account/')
      .reply(200, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.USERINFO_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountGetUserInfo());
  });

  it ('creates USERINFO_SUCCESS', () => {
    const response = { some: "error" };
    const action = accountActions.getUserInfoError(response);

    expect(action).to.deep.equal({
      type: 'USERINFO_ERROR',
      response
    })
  });

  it ('creates USERINFO_ERROR when profile update was not succesful', (done) => {
    const response = { some: "error" };

    nock(SETTINGS.API_BASE)
      .get('/account/')
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.USERINFO_ERROR, response: response },
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

  it ('creates UPDATEPROFILE_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    }
    const action = accountActions.postUpdateProfileSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.UPDATEPROFILE_SUCCESS,
      response
    })
  });

  it ('creates UPDATEPROFILE_SUCCESS when profile update was succesful', (done) => {
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
      .put('/account/', userCredentials)
      .reply(200, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.UPDATEPROFILE_SUCCESS, response: response },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountUpdateProfile(userCredentials));
  });

  it ('creates UPDATEPROFILE_ERROR', () => {
    const response = {
      "email": ["Another user is already registered with this email address"]
    }
    const action = accountActions.postUpdateProfileError(response);

    expect(action).to.deep.equal({
      type: 'UPDATEPROFILE_ERROR',
      response
    })
  });

  it ('creates UPDATEPROFILE_SUCCESS when profile update was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    }
    
    const response = {
      "email": ["Another user is already registered with this email address"]
    }

    nock(SETTINGS.API_BASE)
      .put('/account/', userCredentials)
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.UPDATEPROFILE_ERROR, response: response },
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

  it ('creates CHANGEPASSWORD_SUCCESS', () => {
    const action = accountActions.postChangePasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.CHANGEPASSWORD_SUCCESS
    })
  });

  it ('creates CHANGEPASSWORD_SUCCESS when profile update was succesful', (done) => {
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
      { type: accountActions.CHANGEPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountChangePassword(passwords));
  });

  it ('creates CHANGEPASSWORD_ERROR', () => {
    const response = {"current_password":["Invalid password."]};
    const action = accountActions.postChangePasswordError(response);

    expect(action).to.deep.equal({
      type: 'CHANGEPASSWORD_ERROR',
      response
    })
  });

  it ('creates CHANGEPASSWORD_ERROR when profile update was not succesful', (done) => {
    const response = {"current_password":["Invalid password."]};
    const passwords = {
      new_password: "123456",
      re_new_password: "123456",
      current_password: "78910"
    }

    nock(SETTINGS.API_BASE)
      .post('/account/password/', passwords)
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.CHANGEPASSWORD_ERROR, response },
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

  it ('creates RESETPASSWORD_SUCCESS', () => {
    const action = accountActions.postResetPasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.RESETPASSWORD_SUCCESS
    })
  });

  it ('creates RESETPASSWORD_SUCCESS when password reset was succesful', (done) => {
    const user = {
      email: 'john@beatles.uk'
    }

    nock(SETTINGS.API_BASE)
      .post('/account/password/reset/', user)
      .reply(200)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.RESETPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetPassword(user));
  });

  it ('creates RESETPASSWORD_ERROR', () => {
    const user = { email: 'john@beatles.uk' }
    const response = { some: "Error"}
    const action = accountActions.postResetPasswordError(response);

    expect(action).to.deep.equal({
      type: 'RESETPASSWORD_ERROR',
      response
    })
  });

  it ('creates RESETPASSWORD_ERROR when password reset was not succesful', (done) => {
    const user = { email: 'john@beatles.uk' }
    const response = { some: "Error" }

    nock(SETTINGS.API_BASE)
      .post('/account/password/reset/', user)
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.RESETPASSWORD_ERROR, response },
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

  it ('creates RESETCONFIRMPASSWORD_SUCCESS', () => {
    const action = accountActions.postResetConfirmPasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.RESETCONFIRMPASSWORD_SUCCESS
    })
  });

  it ('creates RESETCONFIRMPASSWORD_SUCCESS when password reset was succesful', (done) => {
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
      { type: accountActions.RESETCONFIRMPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetConfirmPassword(user));
  });

  it ('creates RESETCONFIRMPASSWORD_ERROR', () => {
    const response = { some: "Error" };
    const action = accountActions.postResetConfirmPasswordError(response);

    expect(action).to.deep.equal({
      type: accountActions.RESETCONFIRMPASSWORD_ERROR,
      response
    });
  });

  it ('creates RESETCONFIRMPASSWORD_ERROR when password reset was not succesful', (done) => {
    const user = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
      new_password: '123456',
      re_new_password: '123456'
    }
    const response = { some: "Error" };

    nock(SETTINGS.API_BASE)
      .post('/account/password/reset/confirm/', user)
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.RESETCONFIRMPASSWORD_ERROR, response },
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

  it ('creates ACTIVATE_SUCCESS', () => {
    const action = accountActions.postActivateSuccess();

    expect(action).to.deep.equal({
      type: accountActions.ACTIVATE_SUCCESS
    })
  });

  it ('creates ACTIVATE_SUCCESS when account activation was succesful', (done) => {
    const data = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
    }

    nock(SETTINGS.API_BASE)
      .post('/account/activate/', data)
      .reply(200)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.ACTIVATE_SUCCESS },
      { type: messageActions.REQUEST_DONE },
      { type: routerActions.ROUTER_REDIRECT, redirectTo: '/account/login/' }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountActivate(data));
  });

  it ('creates ACTIVATE_ERROR', () => {
    const response = { some: "Error" };
    const action = accountActions.postActivateError(response);

    expect(action).to.deep.equal({
      type: accountActions.ACTIVATE_ERROR,
      response
    })
  });

  it ('creates ACTIVATE_ERROR when account activation was not succesful', (done) => {
    const data = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
    };
    const response = { some: "Error" };

    nock(SETTINGS.API_BASE)
      .post('/account/activate/', data)
      .reply(400, response)

    const expectedActions = [
      { type: messageActions.REQUEST_START },
      { type: accountActions.ACTIVATE_ERROR, response },
      { type: messageActions.REQUEST_DONE },
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountActivate(data));
  });
});

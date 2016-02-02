import configureMockStore from 'redux-mock-store';
import thunk from 'redux-thunk';

import Storage from '../test-helper/Storage';

import SETTINGS from '../../src/js/settings';
import * as accountActions from '../../src/js/account/actions';
import * as messageActions from '../../src/js/messages/actions';
import * as routerActions from '../../src/js/core/actions';

const middlewares = [thunk];
const mockStore = configureMockStore(middlewares);

describe('Account: actions', () => {
  let server;

  beforeEach(() => {
    window.sessionStorage = new Storage();
    window.sessionStorage.setItem('auth_token', 's8yc8shch98s');

    server = sinon.fakeServer.create();
    server.autoRespond = true;
  });

  afterEach(() => {
    server.restore();
  });

  /* ********************************************************
   *
   * Login
   *
   * ********************************************************/

  it('creates LOGIN_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
    };
    const action = accountActions.postLoginSuccess(response, true);

    expect(action).to.deep.equal({
      type: accountActions.LOGIN_SUCCESS,
      response,
      rememberMe: true,
    });
  });

  it('creates LOGIN_SUCCESS when login was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      password: '123455',
      rememberMe: true,
    };

    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
      token: '8qwihd8zds87hds78',
    };

    server.respondWith('POST', SETTINGS.API_BASE + '/account/login/', JSON.stringify(response));
    server.respondWith('GET', SETTINGS.API_BASE + '/account/', JSON.stringify(response));

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.LOGIN_SUCCESS, response, rememberMe: true },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
      { type: routerActions.ROUTER_REDIRECT, keepMessages: true, redirectTo: '/dashboard/' },
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.USERINFO_SUCCESS, response, keepMessages: true },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogin(userCredentials));
  });

  it('creates LOGIN_ERROR', () => {
    const response = {
      non_field_errors: ['Unable to login with provided credentials.'],
    };
    const action = accountActions.postLoginError(response);

    expect(action).to.deep.equal({
      type: accountActions.LOGIN_ERROR,
      response,
    });
  });

  it('creates LOGIN_ERROR when login was unsuccesful', (done) => {
    const userCredentials = {
      username: 'John',
      password: '123455',
    };

    const response = {
      non_field_errors: ['Unable to login with provided credentials.'],
    };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/login/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.LOGIN_ERROR, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogin(userCredentials));
  });


  /* ********************************************************
   *
   * Logout
   *
   * ********************************************************/

  it('creates LOGOUT_SUCCESS', () => {
    const action = accountActions.postLogoutSuccess();

    expect(action).to.deep.equal({
      type: accountActions.LOGOUT_SUCCESS,
    });
  });

  it('creates LOGOUT_SUCCESS when logout was succesful', (done) => {
    window.localStorage = new Storage();
    window.localStorage.setItem('auth_token', '8937hds8yh8hsd');

    server.respondWith('POST', SETTINGS.API_BASE + '/account/logout/', '');

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.LOGOUT_SUCCESS },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogout({}));
  });

  it('creates LOGOUT_ERROR', () => {
    const response = { some: 'error' };
    const action = accountActions.postLogoutError(response);

    expect(action).to.deep.equal({
      type: 'LOGOUT_ERROR',
      response,
    });
  });

  it('creates LOGOUT_ERROR when logout was not succesful', (done) => {
    const response = { some: 'error' };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/logout/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.LOGOUT_ERROR, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogout());
  });


  /* ********************************************************
   *
   * Register
   *
   * ********************************************************/

  it('creates REGISTER_SUCCESS', () => {
    const response = {};
    const action = accountActions.postRegisterSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.REGISTER_SUCCESS,
      response,
    });
  });

  it ('creates REGISTER_SUCCESS when registration was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
      password: '123456',
      password_repeat: '123456',
    };
    
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    };

    const loginResponse = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
      token: '8qwihd8zds87hds78',
    };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/register/',
      [201, {}, JSON.stringify(response)]
    );
    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/login/',
      JSON.stringify(loginResponse)
    );
    server.respondWith(
      'GET',
      SETTINGS.API_BASE + '/account/',
      JSON.stringify(response)
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.REGISTER_SUCCESS, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.LOGIN_SUCCESS, response: loginResponse, rememberMe: undefined },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
      { type: routerActions.ROUTER_REDIRECT, keepMessages: true, redirectTo: '/dashboard/' },
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.USERINFO_SUCCESS, response, keepMessages: true },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountRegister(userCredentials));
  });

  it('creates REGISTER_ERROR', () => {
    const response = {
      email: ['Another user is already registered with this email address'],
    };
    const action = accountActions.postRegisterError(response);

    expect(action).to.deep.equal({
      type: accountActions.REGISTER_ERROR,
      response,
    });
  });

  it('creates REGISTER_ERROR when registration was not succesful', (done) => {
    const userCredentials = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
      password: '123456',
      password_repeat: '123456',
    };

    const response = {
      email: ['Another user is already registered with this email address'],
    };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/register/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.REGISTER_ERROR, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
      { type: routerActions.ROUTER_REDIRECT, keepMessages: true, redirectTo: '/account/register/' },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountRegister(userCredentials));
  });


  /* ********************************************************
   *
   * Get user info
   *
   * ********************************************************/

  it('creates USERINFO_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    };
    const action = accountActions.getUserInfoSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.USERINFO_SUCCESS,
      response,
      keepMessages: true,
    });
  });

  it('creates USERINFO_SUCCESS when profile update was succesful', (done) => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    };

    server.respondWith(
      'GET',
      SETTINGS.API_BASE + '/account/',
      [200, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.USERINFO_SUCCESS, response, keepMessages: true },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountGetUserInfo());
  });

  it('creates USERINFO_SUCCESS', () => {
    const response = { some: 'error' };
    const action = accountActions.getUserInfoError(response);

    expect(action).to.deep.equal({
      type: 'USERINFO_ERROR',
      response,
      keepMessages: true,
    });
  });

  it('creates USERINFO_ERROR when profile update was not succesful', (done) => {
    const response = { some: 'error' };

    server.respondWith(
      'GET',
      SETTINGS.API_BASE + '/account/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.USERINFO_ERROR, response, keepMessages: true },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountGetUserInfo());
  });


  /* *******************************************************
   *
   * Update profile
   *
   * *******************************************************/

  it('creates UPDATEPROFILE_SUCCESS', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    };
    const action = accountActions.postUpdateProfileSuccess(response);

    expect(action).to.deep.equal({
      type: accountActions.UPDATEPROFILE_SUCCESS,
      response,
    });
  });

  it('creates UPDATEPROFILE_SUCCESS when profile update was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    };

    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    };

    server.respondWith(
      'PUT',
      SETTINGS.API_BASE + '/account/',
      [200, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.UPDATEPROFILE_SUCCESS, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountUpdateProfile(userCredentials));
  });

  it('creates UPDATEPROFILE_ERROR', () => {
    const response = {
      email: ['Another user is already registered with this email address'],
    };
    const action = accountActions.postUpdateProfileError(response);

    expect(action).to.deep.equal({
      type: 'UPDATEPROFILE_ERROR',
      response,
    });
  });

  it('creates UPDATEPROFILE_SUCCESS when profile update was succesful', (done) => {
    const userCredentials = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon',
    };

    const response = {
      email: ['Another user is already registered with this email address'],
    };

    server.respondWith(
      'PUT',
      SETTINGS.API_BASE + '/account/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.UPDATEPROFILE_ERROR, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountUpdateProfile(userCredentials));
  });


  /* ********************************************************
   *
   * Change password
   *
   * ********************************************************/

  it('creates CHANGEPASSWORD_SUCCESS', () => {
    const action = accountActions.postChangePasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.CHANGEPASSWORD_SUCCESS,
    });
  });

  it('creates CHANGEPASSWORD_SUCCESS when profile update was succesful', (done) => {
    const passwords = {
      new_password: '123456',
      re_new_password: '123456',
      current_password: '78910',
    };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/password/',
      [200, {}, '']
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.CHANGEPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountChangePassword(passwords));
  });

  it('creates CHANGEPASSWORD_ERROR', () => {
    const response = { current_password: ['Invalid password.'] };
    const action = accountActions.postChangePasswordError(response);

    expect(action).to.deep.equal({
      type: 'CHANGEPASSWORD_ERROR',
      response,
    });
  });

  it('creates CHANGEPASSWORD_ERROR when profile update was not succesful', (done) => {
    const response = { current_password: ['Invalid password.'] };
    const passwords = {
      new_password: '123456',
      re_new_password: '123456',
      current_password: '78910',
    };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/password/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.CHANGEPASSWORD_ERROR, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountChangePassword(passwords));
  });

  /* ********************************************************
   *
   * Reset password
   *
   * ********************************************************/

  it('creates RESETPASSWORD_SUCCESS', () => {
    const action = accountActions.postResetPasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.RESETPASSWORD_SUCCESS,
    });
  });

  it('creates RESETPASSWORD_SUCCESS when password reset was succesful', (done) => {
    const user = {
      email: 'john@beatles.uk',
    };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/password/reset/',
      [200, {}, '']
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.RESETPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetPassword(user));
  });

  it('creates RESETPASSWORD_ERROR', () => {
    const response = { some: 'Error' };
    const action = accountActions.postResetPasswordError(response);

    expect(action).to.deep.equal({
      type: 'RESETPASSWORD_ERROR',
      response,
    });
  });

  it('creates RESETPASSWORD_ERROR when password reset was not succesful', (done) => {
    const user = { email: 'john@beatles.uk' };
    const response = { some: 'Error' };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/password/reset/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.RESETPASSWORD_ERROR, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetPassword(user));
  });

  /* ********************************************************
   *
   * Confirm reset password
   *
   * ********************************************************/

  it('creates RESETCONFIRMPASSWORD_SUCCESS', () => {
    const action = accountActions.postResetConfirmPasswordSuccess();

    expect(action).to.deep.equal({
      type: accountActions.RESETCONFIRMPASSWORD_SUCCESS,
    });
  });

  it('creates RESETCONFIRMPASSWORD_SUCCESS when password reset was succesful', (done) => {
    const user = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
      new_password: '123456',
      re_new_password: '123456',
    };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/password/reset/confirm/',
      [200, {}, '']
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.RESETCONFIRMPASSWORD_SUCCESS },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetConfirmPassword(user));
  });

  it('creates RESETCONFIRMPASSWORD_ERROR', () => {
    const response = { some: 'Error' };
    const action = accountActions.postResetConfirmPasswordError(response);

    expect(action).to.deep.equal({
      type: accountActions.RESETCONFIRMPASSWORD_ERROR,
      response,
    });
  });

  it('creates RESETCONFIRMPASSWORD_ERROR when password reset was not succesful', (done) => {
    const user = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
      new_password: '123456',
      re_new_password: '123456',
    };
    const response = { some: 'Error' };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/password/reset/confirm/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.RESETCONFIRMPASSWORD_ERROR, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetConfirmPassword(user));
  });

  /* ********************************************************
   *
   * Activate account
   *
   * ********************************************************/

  it('creates ACTIVATE_SUCCESS', () => {
    const action = accountActions.postActivateSuccess();

    expect(action).to.deep.equal({
      type: accountActions.ACTIVATE_SUCCESS,
    });
  });

  it('creates ACTIVATE_SUCCESS when account activation was succesful', (done) => {
    const data = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
    };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/activate/',
      [200, {}, '']
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.ACTIVATE_SUCCESS },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountActivate(data));
  });

  it('creates ACTIVATE_ERROR', () => {
    const response = { some: 'Error' };
    const action = accountActions.postActivateError(response);

    expect(action).to.deep.equal({
      type: accountActions.ACTIVATE_ERROR,
      response,
    });
  });

  it('creates ACTIVATE_ERROR when account activation was not succesful', (done) => {
    const data = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
    };
    const response = { some: 'Error' };

    server.respondWith(
      'POST',
      SETTINGS.API_BASE + '/account/activate/',
      [400, {}, JSON.stringify(response)]
    );

    const expectedActions = [
      { type: messageActions.REQUEST_START, keepMessages: true },
      { type: accountActions.ACTIVATE_ERROR, response },
      { type: messageActions.REQUEST_DONE, keepMessages: true },
    ];

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountActivate(data));
  });
});

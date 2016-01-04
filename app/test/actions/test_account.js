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
  beforeEach(() => {
    window.localStorage = new Storage();
    window.localStorage.setItem('auth_token', 's8yc8shch98s');
  });

  /* ********************************************************
   *
   * Login
   *
   * ********************************************************/

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

    nock(SETTINGS.API_BASE)
      .get('/account/me/')
      .reply(200, response)

    const expectedActions = [
      { type: accountActions.POST_LOGIN_START },
      { type: accountActions.POST_LOGIN_DONE, response },
      { type: accountActions.GET_USERINFO_START },
      { type: accountActions.GET_USERINFO_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountLogin(userCredentials))
  });


  /* ********************************************************
   *
   * Logout
   *
   * ********************************************************/

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


  /* ********************************************************
   *
   * Register
   *
   * ********************************************************/

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
        last_name: 'Lennon'
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


  /* ********************************************************
   *
   * Get user info
   *
   * ********************************************************/

  it ('creates GET_USERINFO_START', () => {
    const action = accountActions.getUserInfoStart();

    expect(action).to.deep.equal({
      type: accountActions.GET_USERINFO_START
    })
  });

  it ('creates GET_USERINFO_DONE', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    }
    const action = accountActions.getUserInfoDone(response);

    expect(action).to.deep.equal({
      type: accountActions.GET_USERINFO_DONE,
      response
    })
  });

  it ('creates GET_USERINFO_DONE when profile update was succesful', (done) => {
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
      { type: accountActions.GET_USERINFO_START },
      { type: accountActions.GET_USERINFO_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountGetUserInfo());
  });


  /* ********************************************************
   *
   * Update profile
   *
   * ********************************************************/

  it ('creates POST_UPDATEPROFILE_START', () => {
    const action = accountActions.postUpdateProfileStart();

    expect(action).to.deep.equal({
      type: accountActions.POST_UPDATEPROFILE_START
    })
  });

  it ('creates POST_UPDATEPROFILE_DONE', () => {
    const response = {
      username: 'John',
      email: 'john@beatles.uk',
      first_name: 'John',
      last_name: 'Lennon'
    }
    const action = accountActions.postUpdateProfileDone(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_UPDATEPROFILE_DONE,
      response
    })
  });

  it ('creates POST_UPDATEPROFILE_DONE when profile update was succesful', (done) => {
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
      { type: accountActions.POST_UPDATEPROFILE_START },
      { type: accountActions.POST_UPDATEPROFILE_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountUpdateProfile(userCredentials));
  });


  /* ********************************************************
   *
   * Change password
   *
   * ********************************************************/

  it ('creates POST_CHANGEPASSWORD_START', () => {
    const action = accountActions.postChangePasswordStart();

    expect(action).to.deep.equal({
      type: accountActions.POST_CHANGEPASSWORD_START
    })
  });

  it ('creates POST_CHANGEPASSWORD_DONE', () => {
    const response = {}

    const action = accountActions.postChangePasswordDone(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_CHANGEPASSWORD_DONE,
      response
    })
  });

  it ('creates POST_CHANGEPASSWORD_DONE when profile update was succesful', (done) => {
    const passwords = {
      new_password: "123456",
      re_new_password: "123456",
      current_password: "78910"
    }
    
    const response = {};

    nock(SETTINGS.API_BASE)
      .post('/account/password/', passwords)
      .reply(200, response)

    const expectedActions = [
      { type: accountActions.POST_CHANGEPASSWORD_START },
      { type: accountActions.POST_CHANGEPASSWORD_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountChangePassword(passwords));
  });

  /* ********************************************************
   *
   * Reset password
   *
   * ********************************************************/

  it ('creates POST_RESETPASSWORD_START', () => {
    const action = accountActions.postResetPasswordStart();

    expect(action).to.deep.equal({
      type: accountActions.POST_RESETPASSWORD_START
    })
  });

  it ('creates POST_RESETPASSWORD_DONE', () => {
    const response = {}

    const action = accountActions.postResetPasswordDone(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_RESETPASSWORD_DONE,
      response
    })
  });

  it ('creates POST_RESETPASSWORD_DONE when password change was succesful', (done) => {
    const user = {
      email: 'john@beatles.uk'
    }
    
    const response = {};

    nock(SETTINGS.API_BASE)
      .post('/account/password/reset/', user)
      .reply(200, response)

    const expectedActions = [
      { type: accountActions.POST_RESETPASSWORD_START },
      { type: accountActions.POST_RESETPASSWORD_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetPassword(user));
  });

  /* ********************************************************
   *
   * Confirm reset password
   *
   * ********************************************************/

  it ('creates POST_RESETCONFIRMPASSWORD_START', () => {
    const action = accountActions.postResetConfirmPasswordStart();

    expect(action).to.deep.equal({
      type: accountActions.POST_RESETCONFIRMPASSWORD_START
    })
  });

  it ('creates POST_RESETCONFIRMPASSWORD_DONE', () => {
    const response = {}

    const action = accountActions.postResetConfirmPasswordDone(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_RESETCONFIRMPASSWORD_DONE,
      response
    })
  });

  it ('creates POST_RESETCONFIRMPASSWORD_DONE when password reset was succesful', (done) => {
    const user = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
      new_password: '123456',
      re_new_password: '123456'
    }
    
    const response = {};

    nock(SETTINGS.API_BASE)
      .post('/account/password/reset/confirm/', user)
      .reply(200, response)

    const expectedActions = [
      { type: accountActions.POST_RESETCONFIRMPASSWORD_START },
      { type: accountActions.POST_RESETCONFIRMPASSWORD_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountResetConfirmPassword(user));
  });

  /* ********************************************************
   *
   * Activate account
   *
   * ********************************************************/

  it ('creates POST_ACTIVATE_START', () => {
    const action = accountActions.postActivateStart();

    expect(action).to.deep.equal({
      type: accountActions.POST_ACTIVATE_START
    })
  });

  it ('creates POST_ACTIVATE_DONE', () => {
    const response = {}

    const action = accountActions.postActivateDone(response);

    expect(action).to.deep.equal({
      type: accountActions.POST_ACTIVATE_DONE,
      response
    })
  });

  it ('creates POST_ACTIVATE_DONE when password reset was succesful', (done) => {
    const data = {
      uid: 'MQ',
      token: '489-963055ee7742ad6c4440',
    }
    
    const response = {};

    nock(SETTINGS.API_BASE)
      .post('/account/activate/', data)
      .reply(200, response)

    const expectedActions = [
      { type: accountActions.POST_ACTIVATE_START },
      { type: accountActions.POST_ACTIVATE_DONE, response }
    ]

    const store = mockStore({}, expectedActions, done);
    store.dispatch(accountActions.accountActivate(data));
    done();
  });
});
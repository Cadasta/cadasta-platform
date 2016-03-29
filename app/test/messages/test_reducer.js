import { Map, List, fromJS, is } from 'immutable';
import { expect } from 'chai';

import messages from '../../src/js/messages/reducer';

describe('messages reducer', () => {
  it('handles REQUEST_START', () => {
    const state = fromJS({ requestsPending: 0 });
    const action = { type: 'REQUEST_START' };

    const nextState = messages(state, action);
    const requestsPending = nextState.get('requestsPending');

    expect(requestsPending).to.deep.equal(1);
  });

  it('handles REQUEST_DONE', () => {
    const state = fromJS({ requestsPending: 1 });
    const action = { type: 'REQUEST_DONE' };

    const nextState = messages(state, action);
    const requestsPending = nextState.get('requestsPending');

    expect(requestsPending).to.equal(0);
  });

  it('handles DISMISS_MESSAGES', () => {
    const state = fromJS({
      requestsPending: 0,
      userFeedback: [
        'Test Message',
      ],
    });

    const action = { type: 'DISMISS_MESSAGES' };

    const nextState = messages(state, action);
    const requestsPending = nextState.get('userFeedback').count();

    expect(requestsPending).to.deep.equal(0);
  });

  it('handles LOGIN_SUCCESS', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = { type: 'LOGIN_SUCCESS' };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'success',
        msg: 'Successfully logged in.',
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles LOGIN_ERROR', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = {
      type: 'LOGIN_ERROR',
      response: {
        non_field_errors: ['Unable to login with provided credentials.'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to login with provided username and password.',
        details: [
          'Unable to login with provided credentials.',
        ],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles LOGOUT_SUCCESS', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = { type: 'LOGOUT_SUCCESS' };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'success',
        msg: 'Successfully logged out.',
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles LOGOUT_ERROR', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = {
      type: 'LOGOUT_ERROR',
      response: {
        non_field_errors: ['Unable to logout with provided credentials.'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to logout.',
        details: [
          'Unable to logout with provided credentials.',
        ],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles REGISTER_SUCCESS', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = { type: 'REGISTER_SUCCESS' };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'success',
        msg: 'Successfully registered.',
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles REGISTER_ERROR', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = {
      type: 'REGISTER_ERROR',
      response: {
        email: ['Another user is already registered with this email address'],
        username: ['A user with that username already exists.'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to register with provided credentials.',
        details: [
          'Another user is already registered with this email address',
          'A user with that username already exists.',
        ],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles CHANGEPASSWORD_SUCCESS', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = { type: 'CHANGEPASSWORD_SUCCESS' };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'success',
        msg: 'Successfully changed password.',
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles CHANGEPASSWORD_ERROR', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = {
      type: 'CHANGEPASSWORD_ERROR',
      response: {
        current_password: ['Invalid password.'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to change password.',
        details: [
          'Invalid password.',
        ],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles UPDATEPROFILE_SUCCESS', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = { type: 'UPDATEPROFILE_SUCCESS' };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'success',
        msg: 'Successfully updated profile information.',
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles UPDATEPROFILE_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'UPDATEPROFILE_ERROR',
      response: {
        email: ['Another user is already registered with this email address'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to update profile.',
        details: [
          'Another user is already registered with this email address',
        ],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles USERINFO_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'USERINFO_ERROR',
      response: {
        email: ['User not found'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to get user profile information from server.',
        details: ['User not found'],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles RESETPASSWORD_SUCCESS', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = { type: 'RESETPASSWORD_SUCCESS' };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'success',
        msg: 'Password successfully reset. Check your inbox for a link to confirm the reset.',
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles RESETPASSWORD_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'RESETPASSWORD_ERROR',
      response: {
        email: ['User not found'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to reset password.',
        details: [
          'User not found',
        ],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles RESETCONFIRMPASSWORD_SUCCESS', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = { type: 'RESETCONFIRMPASSWORD_SUCCESS' };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'success',
        msg: 'Password successfully reset.',
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles RESETCONFIRMPASSWORD_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'RESETCONFIRMPASSWORD_ERROR',
      response: {
        email: ['User not found'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to reset password.',
        details: [
          'User not found',
        ],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles ACTIVATE_SUCCESS', () => {
    const state = new Map({ userFeedback: new List([]) });

    const action = { type: 'ACTIVATE_SUCCESS' };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'success',
        msg: 'Account successfully activated.',
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });

  it('handles ACTIVATE_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'ACTIVATE_ERROR',
      response: {
        email: ['User not found'],
      },
    };
    const nextState = messages(state, action);

    const expected = fromJS({
      userFeedback: [{
        type: 'error',
        msg: 'Unable to activate account.',
        details: [
          'User not found',
        ],
      }],
    });

    expect(is(nextState, expected)).to.be.true;
  });
});

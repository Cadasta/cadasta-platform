import { Map, List, fromJS } from 'immutable';
import {expect} from 'chai';

import messages from '../../src/reducer/messages'

describe('messages reducer', () => {
  it('handles REQUEST_START', () => {
    const state = fromJS({ requestsPending: 0 });
    const action = { type: 'REQUEST_START' };

    const nextState = messages(state, action);
    const requestsPending = nextState.get('requestsPending');

    expect(requestsPending).to.equal(1);
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
          "Test Message"
        ]
    });

    const action = { type: 'DISMISS_MESSAGES' };

    const nextState = messages(state, action);
    const requestsPending = nextState.get('userFeedback').count();

    expect(requestsPending).to.equal(0);
  });

  it('handles POST_LOGIN_SUCCESS', () => {
    const state = Map({ userFeedback: List([]) });

    const action = { type: 'POST_LOGIN_SUCCESS' };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'success',
        msg: "Successfully logged in."
      }]
    }));
  });

  it('handles POST_LOGIN_ERROR', () => {
    const state = Map({ userFeedback: List([]) });

    const action = {
      type: 'POST_LOGIN_ERROR',
      response: {
        "non_field_errors": ["Unable to login with provided credentials."]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to login.",
        details: [
          "Unable to login with provided credentials."
        ]
      }]
    }));
  });

  it('handles POST_LOGOUT_SUCCESS', () => {
    const state = Map({ userFeedback: List([]) });

    const action = { type: 'POST_LOGOUT_SUCCESS' };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'success',
        msg: "Successfully logged out."
      }]
    }));
  });

  it('handles POST_LOGOUT_ERROR', () => {
    const state = Map({ userFeedback: List([]) });

    const action = {
      type: 'POST_LOGOUT_ERROR',
      response: {
        "non_field_errors": ["Unable to logout with provided credentials."]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to logout.",
        details: [
          "Unable to logout with provided credentials."
        ]
      }]
    }));
  });

  it('handles POST_REGISTER_SUCCESS', () => {
    const state = Map({ userFeedback: List([]) });

    const action = { type: 'POST_REGISTER_SUCCESS' };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'success',
        msg: "Successfully registered. You can now log in."
      }]
    }));
  });

  it("handles POST_REGISTER_ERROR", () => {
    const state = Map({ userFeedback: List([]) });

    const action = {
      type: 'POST_REGISTER_ERROR',
      response: {
        "email": ["Another user is already registered with this email address"],
        "username": ["A user with that username already exists."]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to register with provided credentials.",
        details: [
          "Another user is already registered with this email address",
          "A user with that username already exists."
        ]
      }]
    }));
  });

  it('handles POST_CHANGEPASSWORD_SUCCESS', () => {
    const state = Map({ userFeedback: List([]) });

    const action = { type: 'POST_CHANGEPASSWORD_SUCCESS' };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'success',
        msg: "Successfully changed password."
      }]
    }));
  });

  it("handles POST_CHANGEPASSWORD_ERROR", () => {
    const state = Map({ userFeedback: List([]) });

    const action = {
      type: 'POST_CHANGEPASSWORD_ERROR',
      response: {
        "current_password": ["Invalid password."]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to change password.",
        details: [
          "Invalid password."
        ]
      }]
    }));
  });

  it('handles POST_UPDATEPROFILE_SUCCESS', () => {
    const state = Map({ userFeedback: List([]) });

    const action = { type: 'POST_UPDATEPROFILE_SUCCESS' };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'success',
        msg: "Successfully updated profile information."
      }]
    }));
  });

  it('handles POST_UPDATEPROFILE_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'POST_UPDATEPROFILE_ERROR',
      response: {
        "email": ["Another user is already registered with this email address"]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to update profile.",
        details: [
          "Another user is already registered with this email address"
        ]
      }]
    }));
  });

  it('handles GET_USERINFO_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'GET_USERINFO_ERROR',
      response: {
        "email": ["User not found"]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to get user profile information from server.",
        details: [
          "User not found"
        ]
      }]
    }));
  });

  it('handles POST_RESETPASSWORD_SUCCESS', () => {
    const state = Map({ userFeedback: List([]) });

    const action = { type: 'POST_RESETPASSWORD_SUCCESS' };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'success',
        msg: "Password successfully reset. You have recieved an email to confirm the reset."
      }]
    }));
  });

  it('handles POST_RESETPASSWORD_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'POST_RESETPASSWORD_ERROR',
      response: {
        "email": ["User not found"]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to reset password.",
        details: [
          "User not found"
        ]
      }]
    }));
  });

  it('handles POST_RESETCONFIRMPASSWORD_SUCCESS', () => {
    const state = Map({ userFeedback: List([]) });

    const action = { type: 'POST_RESETCONFIRMPASSWORD_SUCCESS' };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'success',
        msg: "Password successfully reset."
      }]
    }));
  });

  it('handles POST_RESETCONFIRMPASSWORD_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'POST_RESETCONFIRMPASSWORD_ERROR',
      response: {
        "email": ["User not found"]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to reset password.",
        details: [
          "User not found"
        ]
      }]
    }));
  });

  it('handles GET_ACTIVATE_SUCCESS', () => {
    const state = Map({ userFeedback: List([]) });

    const action = { type: 'GET_ACTIVATE_SUCCESS' };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'success',
        msg: "Account successfully activated."
      }]
    }));
  });

  it('handles GET_ACTIVATE_ERROR', () => {
    const state = fromJS({ userFeedback: [] });

    const action = {
      type: 'GET_ACTIVATE_ERROR',
      response: {
        "email": ["User not found"]
      }
    };
    const nextState = messages(state, action);

    expect(nextState).to.equal(fromJS({
      userFeedback: [{
        type: 'error',
        msg: "Unable to activate account.",
        details: [
          "User not found"
        ]
      }]
    }));
  });
});
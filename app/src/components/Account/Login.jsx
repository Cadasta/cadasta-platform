import React from 'react';
import { bindActionCreators } from 'redux';
import { connect } from 'react-redux';

import * as accountActions from '../../actions/account';


export const Login = React.createClass({
  handleFormSubmit: function(e) {
    e.preventDefault();

    let userCredentials = {
      username: this.refs.username.value,
      password: this.refs.password.value,
      rememberMe: this.refs.rememberMe.checked
    }

    if (this.props.location && 
        this.props.location.state && 
        this.props.location.state.nextPathname) {
      userCredentials.redirectTo = this.props.location.state.nextPathname;
    }

    this.props.accountLogin(userCredentials);
  },

  render: function() {
    return (
      <form className="login-form" onSubmit={this.handleFormSubmit}>
        <label htmlFor="username">Username</label>
        <input name="username" ref="username" />
        
        <label htmlFor="password">Password</label>
        <input name="password" ref="password" type="password" />

        <input name="rememberMe" ref="rememberMe" type="checkbox" />
        <label htmlFor="rememberMe">Remember Me</label>

        <button type="submit">Login</button>
      </form>
    )
  }
});

function mapStateToProps(state) {
  return {};
}

function mapDispatchToProps(dispatch) {
  return { 
    actions: bindActionCreators(
      Object.assign({}, accountActions, messageActions),
      dispatch
    )
  }
}


export const LoginContainer = connect(
  mapStateToProps,
  accountActions
)(Login);


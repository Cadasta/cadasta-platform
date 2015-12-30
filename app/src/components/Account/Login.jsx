import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../../actions/account';


export const Login = React.createClass({
  handleFormSubmit: function(e) {
    e.preventDefault();
    this.props.accountLogin({
      username: this.refs.username.value,
      password: this.refs.password.value
    });
  },

  render: function() {
    return (
      <form className="login-form" onSubmit={this.handleFormSubmit}>
        <label htmlFor="username">Username</label>
        <input name="username" ref="username" />
        
        <label htmlFor="password">Password</label>
        <input name="password" ref="password" type="password" />

        <button type="submit">Login</button>
      </form>
    )
  }
});

function mapStateToProps(state) {
  return {};
}

export const LoginContainer = connect(
  mapStateToProps,
  accountActions
)(Login);


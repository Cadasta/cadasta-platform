import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../actions';

const propTypes = {
  accountLogin: React.PropTypes.func.isRequired,
  location: React.PropTypes.shape({
    state: React.PropTypes.shape({
      nextPathname: React.PropTypes.string,
    }),
  }),
};


export class Login extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(e) {
    e.preventDefault();

    const userCredentials = {
      username: this.refs.username.value,
      password: this.refs.password.value,
      rememberMe: this.refs.rememberMe.checked,
    };

    if (this.props.location &&
        this.props.location.state &&
        this.props.location.state.nextPathname) {
      userCredentials.redirectTo = this.props.location.state.nextPathname;
    }

    this.props.accountLogin(userCredentials);
  }

  render() {
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
    );
  }
}

Login.propTypes = propTypes;

function mapStateToProps() {
  return {};
}

export const LoginContainer = connect(
  mapStateToProps,
  accountActions
)(Login);

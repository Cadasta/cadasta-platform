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

const contextTypes = {
  intl: React.PropTypes.object,
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
    const labels = this.context.intl.getMessage('labels');

    return (
      <form className="login-form" onSubmit={this.handleFormSubmit}>
        <label htmlFor="username">{ labels.username }</label>
        <input name="username" ref="username" />

        <label htmlFor="password">{ labels.password }</label>
        <input name="password" ref="password" type="password" />

        <input name="rememberMe" ref="rememberMe" type="checkbox" />
        <label htmlFor="rememberMe">{ labels.rememberMe }</label>

        <button type="submit">{ labels.login }</button>
      </form>
    );
  }
}

Login.propTypes = propTypes;
Login.contextTypes = contextTypes;

function mapStateToProps() {
  return {};
}

export const LoginContainer = connect(
  mapStateToProps,
  accountActions
)(Login);

import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../actions';
import { t } from '../../i18n';

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
    return (
      <form className="login-form" onSubmit={this.handleFormSubmit}>
        <label htmlFor="username">{ t('Username') }</label>
        <input name="username" ref="username" />

        <label htmlFor="password">{ t('Password') }</label>
        <input name="password" ref="password" type="password" />

        <input name="rememberMe" ref="rememberMe" type="checkbox" />
        <label htmlFor="rememberMe">{ t('Remember me') }</label>

        <button type="submit">{ t('Login') }</button>
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

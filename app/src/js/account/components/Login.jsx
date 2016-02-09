import React from 'react';
import connect from 'react-redux/lib/components/connect';
import Link from '../../core/components/Link';

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
      <form className="login-form form-narrow" onSubmit={this.handleFormSubmit}>

        <h1>{ t('Sign in to your account') }</h1>

        <div className="form-group">
          <label htmlFor="username">{ t('Username') }</label>
          <input name="username" ref="username" className="form-control input-lg" />
        </div>

        <div className="form-group">
          <label htmlFor="password">{ t('Password') }</label>
          <input name="password" ref="password" type="password" className="form-control input-lg" />
        </div>

        <div className="checkbox">
          <label htmlFor="rememberMe">
          <input name="rememberMe" ref="rememberMe" type="checkbox" />
          { t('Remember me') }</label>
        </div>

        <button type="submit" className="btn btn-default btn-lg btn-block text-uppercase">{ t('Sign In') }</button>

        <p className="text-center">Don't have an account? <Link to={ "/account/register/" }>Register here</Link></p>

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

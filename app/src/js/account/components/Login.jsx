import React from 'react';
import connect from 'react-redux/lib/components/connect';

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
      <form className="login-form form-narrow" onSubmit={this.handleFormSubmit}>
 
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input name="username" ref="username" className="form-control" />
        </div>

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input name="password" ref="password" type="password" className="form-control" />
        </div>

        <div className="checkbox">
          <label htmlFor="rememberMe">
          <input name="rememberMe" ref="rememberMe" type="checkbox" />
          Remember Me</label>
        </div>

        <div className="text-center">
          <button type="submit" className="btn btn-primary btn-lg">Login</button>
        </div>

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

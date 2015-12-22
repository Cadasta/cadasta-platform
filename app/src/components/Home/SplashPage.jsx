import React from 'react';
import { connect } from 'react-redux';


export default class SplashPage extends React.Component {
  handleFormSubmit() {
    this.props.accountLogin({
      username: this.refs.username.value,
      password: this.refs.password.value
    });
  }

  render() {
    return (
      <div className="login-form">
        <label htmlFor="username">Username</label>
        <input name="username" ref="username" />
        
        <label htmlFor="password">Password</label>
        <input name="password" ref="password" type="password" />

        <button type="submit" onClick={ this.handleFormSubmit.bind(this) }>Login</button>
      </div>
    )
  }
}

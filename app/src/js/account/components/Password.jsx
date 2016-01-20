import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../actions';

const propTypes = {
  accountChangePassword: React.PropTypes.func.isRequired,
};

export class Password extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(e) {
    e.preventDefault();
    this.props.accountChangePassword({
      new_password: this.refs.new_password.value,
      current_password: this.refs.current_password.value,
      re_new_password: this.refs.re_new_password.value,
    });
  }

  render() {
    return (
      <form onSubmit={this.handleFormSubmit}>
        <label htmlFor="new_password">New password</label>
        <input type="password" name="new_password" ref="new_password" />

        <label htmlFor="new_password">Repeat new password</label>
        <input type="password" name="re_new_password" ref="re_new_password" />

        <label htmlFor="current_password">Current password</label>
        <input type="password" name="current_password" ref="current_password" />

        <button type="submit">Change password</button>
      </form>
    );
  }
}

Password.propTypes = propTypes;

function mapStateToProps() {
  return {};
}


export const PasswordContainer = connect(
  mapStateToProps,
  accountActions
)(Password);

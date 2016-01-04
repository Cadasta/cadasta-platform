import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../../actions/account';


export const PasswordReset = React.createClass({
  handleFormSubmit: function(e) {
    e.preventDefault();
    this.props.accountResetPassword({
      email: this.refs.email.value
    })
  },

  render: function() {
    return (
      <form onSubmit={this.handleFormSubmit}>
        <label htmlFor="email">Enter email</label>
        <input type="email" name="email" ref="email" />

        <button type="submit">Reset password</button>
      </form>
    )
  }
});

function mapStateToProps(state) {
  return {};
}


export const PasswordResetContainer = connect(
  mapStateToProps,
  accountActions
)(PasswordReset);
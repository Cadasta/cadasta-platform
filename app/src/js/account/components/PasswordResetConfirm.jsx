import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../actions';

const propTypes = {
  accountResetConfirmPassword: React.PropTypes.func.isRequired,
  params: React.PropTypes.shape({
    uid: React.PropTypes.string.isRequired,
    token: React.PropTypes.string.isRequired,
  }),
};

export class PasswordResetConfirm extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(e) {
    e.preventDefault();
    this.props.accountResetConfirmPassword({
      new_password: this.refs.new_password.value,
      re_new_password: this.refs.re_new_password.value,
      uid: this.props.params.uid,
      token: this.props.params.token,
    });
  }

  render() {
    return (
      <form onSubmit={this.handleFormSubmit}>
        <label htmlFor="new_password">Enter new password</label>
        <input type="password" name="new_password" ref="new_password" />

        <label htmlFor="re_new_password">Retype newpassword</label>
        <input type="password" name="re_new_password" ref="re_new_password" />

        <button type="submit">Reset password</button>
      </form>
    );
  }
}

PasswordResetConfirm.propTypes = propTypes;

function mapStateToProps() {
  return {};
}


export const PasswordResetConfirmContainer = connect(
  mapStateToProps,
  accountActions
)(PasswordResetConfirm);

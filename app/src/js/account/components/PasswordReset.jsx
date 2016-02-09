import React from 'react';
import connect from 'react-redux/lib/components/connect';

import { t } from '../../i18n';
import * as accountActions from '../actions';

const propTypes = {
  accountResetPassword: React.PropTypes.func.isRequired,
};

export class PasswordReset extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(e) {
    e.preventDefault();
    this.props.accountResetPassword({
      email: this.refs.email.value,
    });
  }

  render() {
    return (
<<<<<<< HEAD
      <form className="form-narrow" onSubmit={this.handleFormSubmit}>

        <h1>Reset your password</h1>

        <div className="form-group">
          <label htmlFor="email">Enter email</label>
          <input type="email" name="email" ref="email" className="form-control input-lg" />
        </div>

        <button type="submit" className="btn btn-default btn-lg btn-block text-uppercase">Reset password</button>
=======
      <form onSubmit={this.handleFormSubmit}>
        <label htmlFor="email">{ t('Enter email') }</label>
        <input type="email" name="email" ref="email" />

        <button type="submit">{ t('Reset password') }</button>
>>>>>>> master
      </form>
    );
  }
}

PasswordReset.propTypes = propTypes;

function mapStateToProps() {
  return {};
}


export const PasswordResetContainer = connect(
  mapStateToProps,
  accountActions
)(PasswordReset);

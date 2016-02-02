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
      <form onSubmit={this.handleFormSubmit}>
        <label htmlFor="email">{ t('Enter email') }</label>
        <input type="email" name="email" ref="email" />

        <button type="submit">{ t('Reset password') }</button>
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

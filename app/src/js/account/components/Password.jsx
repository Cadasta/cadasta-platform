import React from 'react';
import connect from 'react-redux/lib/components/connect';

import { t } from '../../i18n';
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
<<<<<<< HEAD
      <form onSubmit={this.handleFormSubmit} className="form-narrow">

        <h1>Change your password</h1>

        <div className="form-group">
          <label htmlFor="current_password">Current password</label>
          <input type="password" name="current_password" ref="current_password" className="form-control input-lg" />
        </div>

        <div className="form-group">
          <label htmlFor="new_password">New password</label>
          <input type="password" name="new_password" ref="new_password" className="form-control input-lg" />
        </div>

        <div className="form-group">
          <label htmlFor="new_password">Repeat new password</label>
          <input type="password" name="re_new_password" ref="re_new_password" className="form-control input-lg" />
        </div>

        <button type="submit" className="btn btn-default btn-lg btn-block text-uppercase">Change password</button>
=======
      <form onSubmit={this.handleFormSubmit}>
        <label htmlFor="new_password">{ t('New password') }</label>
        <input type="password" name="new_password" ref="new_password" />

        <label htmlFor="new_password">{ t('Repeat new password') }</label>
        <input type="password" name="re_new_password" ref="re_new_password" />

        <label htmlFor="current_password">{ t('Current password') }</label>
        <input type="password" name="current_password" ref="current_password" />

        <button type="submit">{ t('Change password') }</button>
>>>>>>> master
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

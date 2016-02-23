import React from 'react';
import connect from 'react-redux/lib/components/connect';

import { t } from '../../i18n';
import * as accountActions from '../actions';

import Formsy from 'formsy-react';
import FRC from 'formsy-react-components';
const { Form } = Formsy;
const { Input } = FRC;


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

  handleFormSubmit(data) {
    const password = data;

    password.uid = this.props.params.uid;
    password.token = this.props.params.token;

    this.props.accountResetConfirmPassword(data);
  }

  render() {
    return (
      <Form
        className="form-narrow"
        onValidSubmit={this.handleFormSubmit}
        ref="form"
      >
        <h1>{ t('Create a new password') }</h1>

        <Input
          name="new_password"
          ref="new_password"
          layout="vertical"
          label={ t('New password') }
          className="form-control input-lg"
          type="password"
          validations="minLength:6"
          validationErrors={{
            minLength: t('Your password must be at least 6 characters long.'),
            isDefaultRequiredValue: t('This field is required'),
          }}
          required
        />

        <Input
          name="re_new_password"
          ref="re_new_password"
          layout="vertical"
          label={ t('Repeat new password') }
          className="form-control input-lg"
          type="password"
          validations="equalsField:new_password"
          validationErrors={{
            equalsField: t('Passwords must match.'),
            isDefaultRequiredValue: t('This field is required'),
          }}
          required
        />

        <button
          type="submit"
          formNoValidate
          className="btn btn-default btn-lg btn-block text-uppercase"
        >
          { t('Reset password') }
        </button>
      </Form>
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

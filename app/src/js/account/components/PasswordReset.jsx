import React from 'react';
import connect from 'react-redux/lib/components/connect';

import { t } from '../../i18n';
import * as accountActions from '../actions';

import Formsy from 'formsy-react';
import FRC from 'formsy-react-components';
const { Form } = Formsy;
const { Input } = FRC;

const propTypes = {
  accountResetPassword: React.PropTypes.func.isRequired,
};

export class PasswordReset extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(data) {
    this.props.accountResetPassword(data);
  }

  render() {
    return (
      <Form
        className="form-narrow"
        onValidSubmit={this.handleFormSubmit}
        ref="form"
      >
        <h1>{ t('Reset your password') }</h1>

        <Input
          name="email"
          ref="email"
          layout="vertical"
          className="form-control input-lg"
          label={ t('Enter email') }
          type="email"
          validations="isEmail"
          validationErrors={{
            isDefaultRequiredValue: t('This field is required'),
            isEmail: t('Please provide a valid email address'),
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

PasswordReset.propTypes = propTypes;

function mapStateToProps() {
  return {};
}


export const PasswordResetContainer = connect(
  mapStateToProps,
  accountActions
)(PasswordReset);

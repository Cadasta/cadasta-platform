import React from 'react';
import connect from 'react-redux/lib/components/connect';

import { t } from '../../i18n';
import * as accountActions from '../actions';

import Formsy from 'formsy-react';
import FRC from 'formsy-react-components';
const { Form } = Formsy;
const { Input } = FRC;

const propTypes = {
  accountChangePassword: React.PropTypes.func.isRequired,
};

export class Password extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(data) {
    this.props.accountChangePassword(data);
  }

  render() {
    return (
      <Form
        className="form-narrow"
        onValidSubmit={this.handleFormSubmit}
        ref="form"
      >
        <h1>{ t('Change your password') }</h1>

        <Input
          name="current_password"
          ref="current_password"
          layout="vertical"
          label={ t('Current password') }
          className="form-control input-lg"
          type="password"
          required
          validationErrors={{
            isDefaultRequiredValue: t('This field is required'),
          }}
        />

        <Input
          name="new_password"
          ref="new_password"
          layout="vertical"
          label={ t('New password') }
          className="form-control input-lg"
          type="password"
          validations="minLength:6"
          validationErrors={{
            isDefaultRequiredValue: t('This field is required'),
            minLength: t('Your password must be at least 6 characters long.'),
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
            isDefaultRequiredValue: t('This field is required'),
            equalsField: t('Passwords must match.'),
          }}
          required
        />

        <button
          type="submit"
          formNoValidate
          className="btn btn-default btn-lg btn-block text-uppercase"
        >
          { t('Change password') }
        </button>
      </Form>
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

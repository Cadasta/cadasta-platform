import React from 'react';

import Link from '../../core/components/Link';
import { t } from '../../i18n';

import Formsy from 'formsy-react';
import FRC from 'formsy-react-components';
const { Form } = Formsy;
const { Input } = FRC;

const propTypes = {
  accountRegister: React.PropTypes.func.isRequired,
};

class RegistrationForm extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(data) {
    this.props.accountRegister(data);
  }

  render() {
    return (
      <Form
        className="account-register form-narrow"
        onValidSubmit={this.handleFormSubmit}
        ref="form"
      >
        <h1>{ t('Sign up for a free account') }</h1>

        <Input
          name="username"
          ref="username"
          layout="vertical"
          className="form-control input-lg"
          label={ t('Choose username') }
          type="text"
          required
          validationErrors={{
            isDefaultRequiredValue: t('This field is required'),
          }}
        />

        <Input
          name="email"
          ref="email"
          layout="vertical"
          className="form-control input-lg"
          label={ t('Email') }
          type="email"
          validations="isEmail"
          validationErrors={{
            isEmail: t('Please provide a valid email address'),
            isDefaultRequiredValue: t('This field is required'),
          }}
          required
        />

        <Input
          name="password"
          ref="password"
          layout="vertical"
          label={ t('Password') }
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
          name="password_repeat"
          ref="password_repeat"
          layout="vertical"
          label={ t('Confirm password') }
          className="form-control input-lg"
          type="password"
          validations="equalsField:password"
          validationErrors={{
            equalsField: t('Passwords must match.'),
            isDefaultRequiredValue: t('This field is required'),
          }}
          required
        />

        <Input
          name="first_name"
          ref="first_name"
          layout="vertical"
          className="form-control input-lg"
          label={ t('First name') }
          type="text"
        />

        <Input
          name="last_name"
          ref="last_name"
          layout="vertical"
          className="form-control input-lg"
          label={ t('Last name') }
          type="text"
        />

        <button
          name="register"
          type="submit"
          formNoValidate
          className="btn btn-default btn-lg btn-block text-uppercase"
        >
          { t('Register') }
        </button>

        <p className="text-center">
          Already have an account? <Link to={ "/account/login/" }>Sign in</Link>
        </p>
      </Form>
    );
  }
}

RegistrationForm.propTypes = propTypes;

export default RegistrationForm;

import React from 'react';
import connect from 'react-redux/lib/components/connect';
import Link from '../../core/components/Link';

import * as accountActions from '../actions';
import { t } from '../../i18n';

import Formsy from 'formsy-react';
import FRC from 'formsy-react-components';
const { Form } = Formsy;
const { Input, Checkbox } = FRC;


const propTypes = {
  accountLogin: React.PropTypes.func.isRequired,
  location: React.PropTypes.shape({
    state: React.PropTypes.shape({
      nextPathname: React.PropTypes.string,
    }),
  }),
};

const contextTypes = {
  intl: React.PropTypes.object,
};

export class Login extends React.Component {
  constructor(props) {
    super(props);

    this.handleFormSubmit = this.handleFormSubmit.bind(this);
  }

  handleFormSubmit(data) {
    const userCredentials = data;
    if (this.props.location &&
        this.props.location.state &&
        this.props.location.state.nextPathname) {
      userCredentials.redirectTo = this.props.location.state.nextPathname;
    }

    this.props.accountLogin(userCredentials);
  }

  render() {
    return (
      <Form className="login-form form-narrow" onValidSubmit={this.handleFormSubmit}>
        <h1>{ t('Sign in to your account') }</h1>

        <Input
          name="username"
          ref="username"
          layout="vertical"
          className="form-control input-lg"
          label={ t('Username') }
          type="text"
          required
          validationErrors={{
            isDefaultRequiredValue: t('This field is required'),
          }}
        />

        <Input
          name="password"
          ref="password"
          layout="vertical"
          label={ t('Password') }
          className="form-control input-lg"
          type="password"
          required
          validationErrors={{
            isDefaultRequiredValue: t('This field is required'),
          }}
        />

        <p className="small pull-right">
          <Link to={ "/account/password/reset/" }>{ t('Forgotten password?') }</Link>
        </p>

        <Checkbox
          name="rememberMe"
          ref="rememberMe"
          layout="elementOnly"
          label={t('Remember me')}
        />

        <button
          name="sign-in"
          type="submit"
          formNoValidate
          className="btn btn-default btn-lg btn-block text-uppercase"
        >
          { t('Sign in') }
        </button>

        <p className="text-center">
          Don't have an account? <Link to={ "/account/register/" }>Register here</Link>
        </p>
      </Form>
    );
  }
}

Login.propTypes = propTypes;
Login.contextTypes = contextTypes;

function mapStateToProps() {
  return {};
}

export const LoginContainer = connect(
  mapStateToProps,
  accountActions
)(Login);

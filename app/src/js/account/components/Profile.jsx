import React from 'react';
import connect from 'react-redux/lib/components/connect';
import Link from '../../core/components/Link';

import { t } from '../../i18n';
import * as accountActions from '../actions';

import Formsy from 'formsy-react';
import FRC from 'formsy-react-components';
const { Form } = Formsy;
const { Input } = FRC;


const propTypes = {
  user: React.PropTypes.object.isRequired,
  accountUpdateProfile: React.PropTypes.func.isRequired,
};

export class Profile extends React.Component {
  constructor(props) {
    super(props);

    this.state = this.getStateFromProps(props);

    this.componentWillReceiveProps = this.componentWillReceiveProps.bind(this);
    this.handleFormSubmit = this.handleFormSubmit.bind(this);
    this.getStateFromProps = this.getStateFromProps.bind(this);
  }

  componentWillReceiveProps(nextProps) {
    this.setState(this.getStateFromProps(nextProps));
  }

  getStateFromProps(props) {
    return {
      username: props.user.get('username'),
      email: props.user.get('email'),
      first_name: props.user.get('first_name'),
      last_name: props.user.get('last_name'),
    };
  }

  handleFormSubmit(data) {
    this.props.accountUpdateProfile(data);
  }

  render() {
    return (
      <Form
        className="form-narrow"
        onValidSubmit={this.handleFormSubmit}
        ref="form"
      >
        <h1>{ t('Update your profile') }</h1>

        <Input
          name="username"
          ref="username"
          layout="vertical"
          label={ t('Username') }
          className="form-control input-lg"
          type="text"
          required
          value={this.state.username}
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
            isDefaultRequiredValue: t('This field is required'),
            isEmail: t('Please provide a valid email address'),
          }}
          required
          value={this.state.email}
        />

        <Input
          name="first_name"
          ref="first_name"
          layout="vertical"
          className="form-control input-lg"
          label={ t('First name') }
          type="text"
          value={this.state.first_name}
        />

        <Input
          name="last_name"
          ref="last_name"
          layout="vertical"
          className="form-control input-lg"
          label={ t('Last name') }
          type="text"
          value={this.state.last_name}
        />

        <button
          formNoValidate
          type="submit"
          className="btn btn-default btn-lg btn-block text-uppercase"
        >
          { t('Update profile') }
        </button>

        <h5>{ t('Password options') }</h5>
        <ul>
          <li><Link to={ "/account/password/" } >{ t('Change password') }</Link></li>
          <li><Link to={ "/account/password/reset/" }>{ t('Reset password') }</Link></li>
        </ul>
      </Form>
    );
  }
}

Profile.propTypes = propTypes;

function mapStateToProps(state) {
  return {
    user: state.user,
  };
}

export const ProfileContainer = connect(
  mapStateToProps,
  accountActions
)(Profile);

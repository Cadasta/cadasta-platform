import React from 'react';
import connect from 'react-redux/lib/components/connect';

import RegistrationForm from './RegistrationForm';
import * as accountActions from '../actions';

const propTypes = {
  accountRegister: React.PropTypes.func.isRequired,
};

export class Register extends React.Component {
  render() {
    return (
      <div>
        <RegistrationForm accountRegister={this.props.accountRegister} />
      </div>
    );
  }
}

Register.propTypes = propTypes;

function mapStateToProps() {
  return {};
}

export const RegisterContainer = connect(
  mapStateToProps,
  accountActions
)(Register);

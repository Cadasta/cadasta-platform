import React from 'react';
import { connect } from 'react-redux';

import RegistrationForm from './RegistrationForm';
import * as accountActions from '../../actions/account';


export const Register = React.createClass({

  render: function() {
    return (
      <div>
        <RegistrationForm accountRegister={this.props.accountRegister} />
      </div>
    )
  }
});

function mapStateToProps(state) {
  return {};
}

export const RegisterContainer = connect(
  mapStateToProps,
  accountActions
)(Register);

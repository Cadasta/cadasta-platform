import React from 'react';
import { connect } from 'react-redux';

import RegistrationForm from '../../account/components/RegistrationForm';
import * as accountActions from '../../account/actions';

const propTypes = {
  accountRegister: React.PropTypes.func.isRequired,
};

export class Home extends React.Component {
  render() {
    return (
      <div>
        <h2>Welcome.</h2>
        <RegistrationForm accountRegister={this.props.accountRegister} />
      </div>
    );
  }
}

Home.propTypes = propTypes;

function mapStateToProps() {
  return {};
}

export const HomeContainer = connect(
  mapStateToProps,
  accountActions
)(Home);

import React from 'react';
import connect from 'react-redux/lib/components/connect';

import RegistrationForm from '../../account/components/RegistrationForm';
import * as accountActions from '../../account/actions';
import { t } from '../../i18n';

const propTypes = {
  accountRegister: React.PropTypes.func.isRequired,
};

export class Home extends React.Component {
  render() {
    return (
      <div>
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

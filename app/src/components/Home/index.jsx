import React from 'react';
import { connect } from 'react-redux';

import SplashPage from './SplashPage';
import Dashboard from './Dashboard';
import * as accountActions from '../../actions/account';


export class Home extends React.Component {
  render() {
    if (this.props.user.get('auth_token')) {
      return <Dashboard /> 
    } else {
      return <SplashPage accountLogin={this.props.accountLogin} />
    }
  }
};

function mapStateToProps(state) {
  return {
    user: state.get('user')
  };
}

export const HomeContainer = connect(
  mapStateToProps,
  accountActions
)(Home);


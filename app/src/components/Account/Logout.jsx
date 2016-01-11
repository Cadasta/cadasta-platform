import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../../actions/account';

export const Logout =  React.createClass({
  componentWillMount: function() {
    this.props.accountLogout();
  },

  render: function() {
    if (this.props.user.get('auth_token')) {
      return ( <div>Logging out</div> );
    } else {
      return (<div>Successfully logged out</div>);
    }
  }
});

function mapStateToProps(state) {
  return {
    user: state.user
  };
}

export const LogoutContainer = connect(
  mapStateToProps,
  accountActions
)(Logout);
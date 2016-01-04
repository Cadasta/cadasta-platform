import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../../actions/account';

export const Activate = React.createClass({
  componentDidMount: function(e) {
  	this.props.accountActivate({
      uid: this.props.params.uid,
      token: this.props.params.token
    })
  },

  render: function() {
    return (<div/>)
  }
});

function mapStateToProps(state) {
  return {};
}


export const ActivateContainer = connect(
  mapStateToProps,
  accountActions
)(Activate);
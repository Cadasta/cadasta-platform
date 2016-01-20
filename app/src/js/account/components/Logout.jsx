import React from 'react';
import { connect } from 'react-redux';

import * as accountActions from '../actions';

const propTypes = {
  accountLogout: React.PropTypes.func.isRequired,
};

export class Logout extends React.Component {
  constructor(props) {
    super(props);

    this.componentWillMount = this.componentWillMount.bind(this);
  }

  componentWillMount() {
    this.props.accountLogout();
  }

  render() {
    return (<div />);
  }
}

Logout.propTypes = propTypes;

function mapStateToProps(state) {
  return {
    user: state.user,
  };
}

export const LogoutContainer = connect(
  mapStateToProps,
  accountActions
)(Logout);

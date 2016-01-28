import React from 'react';
import connect from 'react-redux/lib/components/connect';

import * as accountActions from '../actions';

const propTypes = {
  accountActivate: React.PropTypes.func.isRequired,
  params: React.PropTypes.shape({
    uid: React.PropTypes.string.isRequired,
    token: React.PropTypes.string.isRequired,
  }),
};

export class Activate extends React.Component {
  constructor(props) {
    super(props);

    this.componentDidMount = this.componentDidMount.bind(this);
  }

  componentDidMount() {
    this.props.accountActivate({
      uid: this.props.params.uid,
      token: this.props.params.token,
    });
  }

  render() {
    return (<div/>);
  }
}

Activate.propTypes = propTypes;

function mapStateToProps() {
  return {};
}

export const ActivateContainer = connect(
  mapStateToProps,
  accountActions
)(Activate);

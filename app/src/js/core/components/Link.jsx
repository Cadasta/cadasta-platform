import React from 'react';
import { Link as RouterLink } from 'react-router';
import { dismissMessages } from '../../messages/actions';

const propTypes = {
  children: React.PropTypes.oneOfType([
    React.PropTypes.object.isRequired,
    React.PropTypes.string.isRequired,
  ]),
};

const contextTypes = {
  store: React.PropTypes.object,
};

class Link extends React.Component {
  constructor(props) {
    super(props);

    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    this.context.store.dispatch(dismissMessages());
  }

  render() {
    return (
      <RouterLink { ...this.props } onClick={ this.handleClick } >{this.props.children}</RouterLink>
    );
  }
}

Link.propTypes = propTypes;
Link.contextTypes = contextTypes;

export default Link;

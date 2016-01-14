import React from 'react';
import { Link as RouterLink } from 'react-router';
import { dismissMessages } from '../../actions/messages.js';

const Link = React.createClass({
  contextTypes: {
    store: React.PropTypes.object
  },

  handleClick: function () {
    this.context.store.dispatch(dismissMessages());
  },

  render: function() {
    return (
      <RouterLink { ...this.props } onClick={ this.handleClick } >{this.props.children}</RouterLink>
    );
  }
});

export default Link;

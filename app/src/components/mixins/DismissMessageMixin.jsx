import React from 'react';

import { dismissMessages } from '../../actions/messages.js';

const DismissMessageMixin = {
  contextTypes: {
    store: React.PropTypes.object
  },

  componentWillUnmount: function() {
    this.context.store.dispatch(dismissMessages());
  }
};

export default DismissMessageMixin;

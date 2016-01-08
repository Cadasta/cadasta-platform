import React from 'react';
import classNames from 'classnames';

const Message = React.createClass({
  dismiss: function() {
    this.props.messageDismiss(this.props.message.get('id'));
  },

  renderDismiss: function() {
    if (this.props.message.get('dismissable')) {
      return <button type="button" onClick={ this.dismiss }>Dismiss</button>
    }
  },

  renderErrorDetail: function () {
    const details = this.props.message.get('details');
    if (details && details.count()) {
      return <ul>{details.map(detail => <li>{ detail }</li>)}</ul>
    }
  },

  render: function() {
    const message = this.props.message;
    const messageClass = classNames('message', message.get('type'));

    return (
      <div className={ messageClass }>
        <p>{ message.get('msg') }</p>
        { this.renderErrorDetail() }
        { this.renderDismiss() }
      </div>
    )
  }
});

export default Message;
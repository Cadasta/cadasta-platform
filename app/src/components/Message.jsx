import React from 'react';

const Message = React.createClass({
  dismiss: function() {
    this.props.messageDismiss(this.props.message.get('id'));
  },

  renderDismiss: function() {
    if (this.props.message.get('dismissable')) {
      return <button type="button" onClick={ this.dismiss }>Dismiss</button>
    }
  },

  render: function() {
    const message = this.props.message;

    return (
      <div className="message { message.get('type') }">
        <p>{ message.get('msg') }</p>
        { this.renderDismiss() }
      </div>
    )
  }
});

export default Message;
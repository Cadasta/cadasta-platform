import React from 'react';

export default class Message extends React.Component {
  dismiss () {
    this.props.messageDismiss(this.props.message.get('id'));
  }

  renderDismiss() {
    if (this.props.message.get('dismissable')) {
      return <button type="button" onClick={ this.dismiss.bind(this) }>Dismiss</button>
    }
  }

  render() {
    const message = this.props.message;

    return (
      <div className="message { message.get('type') }">
        <p>{ message.get('msg') }</p>
        { this.renderDismiss() }
      </div>
    )
  }
}
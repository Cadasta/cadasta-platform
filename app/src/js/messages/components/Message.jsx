import React from 'react';
import classNames from 'classnames';

const propTypes = {
  messageDismiss: React.PropTypes.func,
  message: React.PropTypes.object.isRequired,
};

class Message extends React.Component {
  constructor(props) {
    super(props);
    this.dismiss = this.dismiss.bind(this);
    this.renderDismiss = this.renderDismiss.bind(this);
    this.renderErrorDetail = this.renderErrorDetail.bind(this);
  }

  dismiss() {
    this.props.messageDismiss(this.props.message.get('id'));
  }

  renderDismiss() {
    if (this.props.message.get('dismissable')) {
      return <button type="button" onClick={ this.dismiss }>Dismiss</button>;
    }
  }

  renderErrorDetail() {
    const details = this.props.message.get('details');
    if (details && details.count()) {
      return <ul>{details.map(detail => <li>{ detail }</li>)}</ul>;
    }
  }

  getClassNames(msgType) {
    let classes = ['alert', 'text-center'];
    switch(msgType):
      case 'success':
        classes.push('alert-success');
        break;
      case 'error':
        classes.push('alert-danger');
        break;

    return classNames('message', ...classes);

  }

  render() {
    const message = this.props.message;
    const messageClass = classNames('message', message.get('type'));

    return (
      <div className={ messageClass }>
        <p>{ message.get('msg') }</p>
        { this.renderErrorDetail() }
        { this.renderDismiss() }
      </div>
    );
  }
}

Message.propTypes = propTypes;

export default Message;

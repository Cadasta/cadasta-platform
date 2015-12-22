import React from 'react';
import { connect } from 'react-redux';

import Message from './Message';


export class App extends React.Component {
  render() {
    return (
      <div>
        <div id="messages">
          {this.props.messages.map(msg => <Message key={msg.get('id')} message={msg} />)}        
        </div>
        { this.props.children }
      </div>
    )
  }
}

function mapStateToProps(state) {
  return {
    messages: state.get('messages')
  };
}

export const AppContainer = connect(
  mapStateToProps
)(App);
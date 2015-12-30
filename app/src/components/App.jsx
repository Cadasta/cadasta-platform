import React from 'react';
import { connect } from 'react-redux';
import { Link } from 'react-router'

import Message from './Message';
import { HomeContainer } from './Home';
import Header from './Header';


export const App = React.createClass({
  render: function() {
    return (
      <div>
        <Header user={this.props.user} />
        <div id="messages">
          {this.props.messages.map(msg => <Message key={msg.get('id')} message={msg} />)}        
        </div>
        { this.props.children || <HomeContainer /> }
      </div>
    )
  }
})

function mapStateToProps(state) {
  return {
    messages: state.get('messages'),
    user: state.get('user')
  };
}

export const AppContainer = connect(
  mapStateToProps
)(App);
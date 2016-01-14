import React from 'react';
import { connect } from 'react-redux';
import { Link } from 'react-router'

import Message from './Message';
import { HomeContainer } from './Home';
import Header from './Header';

export const App = React.createClass({
  loadingState: function () {
    if (this.props.messages.get('requestsPending')) {
      return (<div id="loading">Loading ...</div>);
    }
  },

  render: function() {
    return (
      <div>
        <Header user={this.props.user} />

        { this.loadingState() }

        <div id="messages">
          {this.props.messages.get('userFeedback').map(
            msg => <Message key={msg.get('id')} message={msg} />
          )}        
        </div>
        { this.props.children || <HomeContainer /> }
      </div>
    )
  }
})

function mapStateToProps(state) {
  return {
    messages: state.messages,
    user: state.user
  };
}

export const AppContainer = connect(
  mapStateToProps
)(App);
import React from 'react';
import connect from 'react-redux/lib/components/connect';

import Message from '../../messages/components/Message';
import { HomeContainer } from './Home';
import Header from './Header';

const propTypes = {
  messages: React.PropTypes.object.isRequired,
  user: React.PropTypes.object.isRequired,
  children: React.PropTypes.object,
};

export class App extends React.Component {
  loadingState() {
    if (this.props.messages.get('requestsPending')) {
      return (<div id="loading">Loading ...</div>);
    }
  }

  render() {
    return (
      <div className="container-fluid">
        <Header user={this.props.user} />

        { this.loadingState() }

        <div id="messages">
          {this.props.messages.get('userFeedback').map(
            msg => <Message key={msg.get('id')} message={msg} />
          )}
        </div>
        { this.props.children || <HomeContainer /> }
      </div>
    );
  }
}

App.propTypes = propTypes;

function mapStateToProps(state) {
  return {
    messages: state.messages,
    user: state.user,
  };
}

export const AppContainer = connect(
  mapStateToProps
)(App);

import React from 'react';

import SplashPage from './SplashPage'

export default class Dashboard extends React.Component {
  render() {
    return (
      <div>
        <h1>Dashboard</h1>
        <button onClick={ this.props.accountLogout }>Logout</button>
      </div>
    )
  }
}
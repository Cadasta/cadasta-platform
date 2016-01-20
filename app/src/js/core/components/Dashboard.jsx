import React from 'react';
import { connect } from 'react-redux';

export class Dashboard extends React.Component {
  render() {
    return (
      <div>
        <h1>Dashboard</h1>
      </div>
    );
  }
}

function mapStateToProps() {
  return {};
}

export const DashboardContainer = connect(
  mapStateToProps
)(Dashboard);

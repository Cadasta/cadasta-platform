import React from 'react';
import { connect } from 'react-redux';


export const Dashboard = React.createClass({
  render: function() {
    return (
      <div>
        <h1>Dashboard</h1>
      </div>
    )
  }
});

function mapStateToProps(state) {
  return {};
}

export const DashboardContainer = connect(
  mapStateToProps
)(Dashboard);

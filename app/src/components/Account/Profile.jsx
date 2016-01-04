import React from 'react';
import { connect } from 'react-redux';
import { Link } from 'react-router';

import * as accountActions from '../../actions/account';


export const Profile = React.createClass({
  getStateFromProps: function(props) {
    return {
      username: props.user.get('username'),
      email: props.user.get('email'),
      first_name: props.user.get('first_name'),
      last_name: props.user.get('last_name')
    };
  },

  getInitialState: function() {
    return this.getStateFromProps(this.props);
  },

  componentWillReceiveProps: function(nextProps) {
    this.setState(this.getStateFromProps(nextProps));
  },

  handleValueChange(e) {
    this.setState({[e.target.name]: e.target.value});
  },

  handleFormSubmit: function(e) {
    e.preventDefault();
    this.props.accountUpdateProfile({
      username: this.refs.username.value,
      email: this.refs.email.value,
      first_name: this.refs.first_name.value,
      last_name: this.refs.last_name.value,
    })
  },

  render: function() {
    return (
      <div>
        <form className="profile-form" onSubmit={this.handleFormSubmit}>
          <label htmlFor="username">Username</label>
          <input name="username" ref="username" value={this.state.username} onChange={this.handleValueChange} />

          <label htmlFor="email">Email</label>
          <input name="email" ref="email" type="email" value={this.state.email} onChange={this.handleValueChange} />

          <label htmlFor="first_name">First name</label>
          <input name="first_name" ref="first_name" value={this.state.first_name} onChange={this.handleValueChange} />

          <label htmlFor="last_name">Last name</label>
          <input name="last_name" ref="last_name"  value={this.state.last_name} onChange={this.handleValueChange} />

          <button type="submit">Update profile</button>
        </form>

        <div>
          <Link to="/account/password/">Change password</Link>
          <Link to="/account/password/reset/">Reset password</Link>
        </div>
      </div>
      
    )
  }
});

function mapStateToProps(state) {
  return {
    user: state.get('user')
  };
}

export const ProfileContainer = connect(
  mapStateToProps,
  accountActions
)(Profile);
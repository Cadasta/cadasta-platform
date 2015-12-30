import React from 'react';
import { Link } from 'react-router'


const Header = React.createClass({
  getUserLinks: function() {
    if (this.props.user.get('auth_token')) {
      return (
        <ul>
          <li><a href="/account/profile/">Profile</a></li>
          <li><Link to={ "/account/logout/" }>Logout</Link></li>
        </ul>
      )
    } else {
      return (
        <ul>
          <li><Link to={ "/account/login/" }>Login</Link></li>
          <li><a href="/account/register/">Register</a></li>
        </ul>
      )
    }
  },

  render: function() {
    return (
      <div id="header">
        <h1><Link to="/">Cadasta</Link></h1>
        { this.getUserLinks() }
      </div>
    )
  }
});

export default Header;

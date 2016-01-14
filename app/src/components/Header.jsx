import React from 'react';
import Link from './Router/Link';


const Header = React.createClass({
  getUserLinks: function() {
    if (this.props.user.get('auth_token')) {
      return (
        <ul>
          <li><Link to={ "/account/profile/" }>Profile</Link></li>
          <li><Link to={ "/account/logout/" }>Logout</Link></li>
        </ul>
      )
    } else {
      return (
        <ul>
          <li><Link to={ "/account/login/" }>Login</Link></li>
          <li><Link to={ "/account/register/" }>Register</Link></li>
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

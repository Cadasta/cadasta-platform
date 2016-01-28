import React from 'react';
import Link from './Link';

const propTypes = {
  user: React.PropTypes.object.isRequired,
};

class Header extends React.Component {
  constructor(props) {
    super(props);

    this.getUserLinks = this.getUserLinks.bind(this);
  }

  getUserLinks() {
    let userLinks;

    if (this.props.user.get('auth_token')) {
      userLinks = (
        <ul>
          <li><Link to={ "/account/profile/" }>Profile</Link></li>
          <li><Link to={ "/account/logout/" }>Logout</Link></li>
        </ul>
      );
    } else {
      userLinks = (
        <ul>
          <li><Link to={ "/account/login/" }>Login</Link></li>
          <li><Link to={ "/account/register/" }>Register</Link></li>
        </ul>
      );
    }

    return userLinks;
  }

  render() {
    return (
      <div id="header">
        <h1><Link to="/">Cadasta</Link></h1>
        { this.getUserLinks() }
      </div>
    );
  }
}

Header.propTypes = propTypes;

export default Header;

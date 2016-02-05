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
        <div className="user-links pull-right">
          <ul className="list-inline">
            <li><Link to={ "/account/login/" }>Sign In</Link></li>
            <li><Link to={ "/account/register/" }>Register</Link></li>
          </ul>
        </div>
      );
    }

    return userLinks;
  }

  render() {
    return (
      <header>
        <div className="container">
          <h1 id="logo" className="pull-left"><Link to="/"><img src="/img/logo-white-l.png" alt="Cadasta" /></Link></h1>
          { this.getUserLinks() }
        </div>
      </header>
    );
  }
}

Header.propTypes = propTypes;

export default Header;

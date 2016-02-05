import React from 'react';
import Link from './Link';
import { t } from '../../i18n';

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
          <li><Link to={ "/account/profile/" }>{ t('Profile') }</Link></li>
          <li><Link to={ "/account/logout/" }>{ t('Logout') }</Link></li>
        </ul>
      );
    } else {
      userLinks = (
        <ul>
          <li><Link to={ "/account/login/" }>{ t('Login') }</Link></li>
          <li><Link to={ "/account/register/" }>{ t('Register') }</Link></li>
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

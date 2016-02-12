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
        <div className="user-links pull-right">
          <ul className="list-inline">
            <li><Link to={ "/account/profile/" }>{ t('Profile') }</Link></li>
            <li><Link to={ "/account/logout/" }>{ t('Logout') }</Link></li>
          </ul>
        </div>
      );
    } else {
      userLinks = (
        <div className="reg-links pull-right">
          <ul className="list-inline">
            <li><Link to={ "/account/login/" }>{ t('Login') }</Link></li>
            <li><Link to={ "/account/register/" }>{ t('Register') }</Link></li>
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
          <h1 id="logo" className="pull-left"><Link to="/"><img src={require('../../../img/logo-white.png')} /></Link></h1>
          { this.getUserLinks() }
        </div>
      </header>
    );
  }
}

Header.propTypes = propTypes;

export default Header;

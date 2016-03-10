import React from 'react';
import Link from './Link';
import { t } from '../../i18n';

export class Footer extends React.Component {
  render() {
    return (
      <footer className="footer">
        <div className="container">
          <p className="pull-left">Copyright 2016 Cadasta. All Rights Reserved.</p>
          <ul className="list-inline pull-right">
            <li><Link to={ "http://cadasta.org/about-us" }>{ t('About Us') }</Link></li>
            <li><Link to={ "#" }>{ t('Privacy') }</Link></li>
            <li><Link to={ "#" }>{ t('Terms of Service') }</Link></li>
            <li><Link to={ "http://cadasta.org/code-of-conduct" }>{ t('Code of Conduct') }</Link></li>
            <li><Link to={ "http://github.com/Cadasta" }>{ t('Visit us on Github') }</Link></li>
          </ul>
        </div>
      </footer>
    );
  }
}

export default Footer;
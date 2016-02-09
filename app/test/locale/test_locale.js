import React from 'react';
import { shallow } from 'enzyme';

import { setLocale, t, tn, tct } from '../../src/js/i18n';

describe('request', () => {
  beforeEach(() => {
    setLocale('de');
  });

  it('translates a simple string', () => {
    expect(t('Username')).to.equal('Nutzername');
  });

  it('translates an interpolated string', () => {
    expect(t('Hello %(name)s', { name: 'Nicole' })).to.equal('Hallo Nicole');
  });

  it('translates an singular string with zero', () => {
    expect(
      tn('%d unread message', '%d unread messages', 0)
    ).to.equal('0 ungelesene Nachrichten');
  });

  it('translates an singular string', () => {
    expect(
      tn('%d unread message', '%d unread messages', 1)
    ).to.equal('1 ungelesene Nachricht');
  });

  it('translates an plural string', () => {
    expect(
      tn('%d unread message', '%d unread messages', 2)
    ).to.equal('2 ungelesene Nachrichten');
  });

  it('translates a component template', () => {
    const translated = shallow(tct('Need more information? [link:Click here].', {
      link: <a />,
    }));
    expect(translated.text()).to.contain('Für weitere Informationen');

    const link = translated.find('a');
    expect(link.length).to.equal(1);
    expect(link.text()).to.contain('Hier klicken');
  });
});

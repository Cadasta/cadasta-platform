import Jed from 'jed';
import { sprintf } from 'sprintf-js';

import catalogs from '../../locale/catalogs';

const LOCALE_DEBUG = __I18N_DEBUG__ || false;

let jed;
const browserLocale = window.navigator.language || 'en';

const translations = (function translations() {
  const languages = {};

  catalogs.supported_locales.forEach(function (lang) {
    languages[lang] = require('../../locale/' + lang + '/LC_MESSAGES/messages.po');
  });
  return languages;
}());

export function setLocale(locale) {
  const localeCatalogue = translations[locale] || translations.en;

  jed = new Jed({
    missing_key_callback: function missingKeyCallback(key) {
      console.warn('Missing i18n key: ' + key);
    },
    locale_data: {
      messages: localeCatalogue,
    },
  });
}

setLocale(browserLocale);

function mark(str) {
  if (!LOCALE_DEBUG) {
    return str;
  }

  const proxy = {
    $$typeof: Symbol.for('react.element'),
    type: 'span',
    key: null,
    ref: null,
    props: {
      className: 'translation-wrapper',
      children: typeof str === 'array' ? str : [str],
    },
    _owner: null,
    _store: {},
  };

  proxy.toString = function () {
    return '-@-' + str + '-@-';
  };

  return proxy;
}

export function t(str, ...args) {
  let translated = jed.gettext(str);

  if (args && args.length > 0) {
    translated = sprintf(translated, ...args);
  }

  return mark(translated);
}

export function tn(singular, plural, ...args) {
  return mark(sprintf(jed.ngettext(singular, plural, args[0] || 0), args));
}

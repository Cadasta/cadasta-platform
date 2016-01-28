import Jed from 'jed';
import { sprintf } from 'sprintf-js';

import catalogs from '../../locale/catalogs';

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

export function t(str, ...args) {
  let translated = jed.gettext(str);

  if (args && args.length > 0) {
    translated = sprintf(translated, ...args);
  }

  return translated;
}

export function tn(singular, plural, ...args) {
  return sprintf(jed.ngettext(singular, plural, args[0] || 0), args);
}

import de from '../../locale/de-DE';
import en from '../../locale/en-US';

const locales = {};

locales.de = de;
locales.en = de;
locales['de-DE'] = de;
locales['en-US'] = en;

const navigator = window.navigator;

const browserLocale = (navigator.languages[0] ||
    window.navigator.userLanguage ||
    window.navigator.language ||
    'en-US');
const appLocale = (browserLocale in locales ? browserLocale : 'en-US');

export default locales[appLocale];

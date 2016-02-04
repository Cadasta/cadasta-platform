import React from 'react';
import Jed from 'jed';
import { sprintf } from 'sprintf-js';

import catalogs from '../../locale/catalogs';

const LOCALE_DEBUG = __I18N_DEBUG__ || false;

let jed;
const browserLocale = window.navigator.language || 'en';

const translations = (function translations() {
  const languages = {};

  catalogs.supported_locales.forEach(function readLang(lang) {
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

function parseComponentTemplate(string) {
  const rv = {};

  function process(startPos, group, inGroup) {
    const regex = /\[(.*?)(:|\])|\]/g;
    let match;
    const buf = [];
    let satisfied = false;

    let pos = regex.lastIndex = startPos;
    while ((match = regex.exec(string)) !== null) { // eslint-disable-line no-cond-assign
      const substr = string.substr(pos, match.index - pos);
      if (substr !== '') {
        buf.push(substr);
      }

      if (match[0] === ']') {
        if (inGroup) {
          satisfied = true;
          break;
        } else {
          pos = regex.lastIndex;
          continue;
        }
      }

      if (match[2] === ']') {
        pos = regex.lastIndex;
      } else {
        pos = regex.lastIndex = process(regex.lastIndex, match[1], true);
      }
      buf.push({ group: match[1] });
    }

    let endPos = regex.lastIndex;
    if (!satisfied) {
      const rest = string.substr(pos);
      if (rest) {
        buf.push(rest);
      }
      endPos = string.length;
    }

    rv[group] = buf;
    return endPos;
  }

  process(0, 'root', false);

  return rv;
}

function renderComponentTemplate(template, components) {
  let idx = 0;
  function renderGroup(group) {
    const children = [];

    (template[group] || []).forEach((item) => {
      if (typeof item === 'string') {
        children.push(<span key={idx++}>{item}</span>);
      } else {
        children.push(renderGroup(item.group));
      }
    });

    // in case we cannot find our component, we call back to an empty
    // span so that stuff shows up at least.
    let reference = components[group] || <span key={idx++} />;
    if (!React.isValidElement(reference)) {
      reference = <span key={idx++}>{reference}</span>;
    }

    let component;
    if (children.length > 0) {
      component = React.cloneElement(reference, { key: idx++ }, children);
    } else {
      component = React.cloneElement(reference, { key: idx++ });
    }
    return component;
  }

  return renderGroup('root');
}

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

  proxy.toString = function toString() {
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

export function tct(template, components) {
  const tmpl = parseComponentTemplate(jed.gettext(template));
  return mark(renderComponentTemplate(tmpl, components));
}

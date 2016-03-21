var gettextParser = require('gettext-parser');
var fs = require('fs');
var path = require('path');
var cats = require('../src/locale/catalogs.js');


function locfile(lang, format) {
  return path.dirname(__dirname) + '/src/locale/' + lang +
         '/LC_MESSAGES/messages.' + format;
}

for (i in cats.supported_locales) {
  var lang = cats.supported_locales[i];
  var tx = process_po(locfile(lang, 'po'), { format: 'jed' });
  fs.writeFileSync(locfile(lang, 'json'), JSON.stringify(tx, null, 4));
}




function isEmptyMessage(msg) {
  for (var i = 0; i < msg.msgstr.length; i++) {
    if (msg.msgstr[i] === '' || msg.msgstr[i] === null) {
      return true;
    }
  }
  return false;
}

function process_po(source) {
  var srctxt = fs.readFileSync(source, 'UTF-8');
  var catalog = gettextParser.po.parse(srctxt);
  var rv = {};
  for (var msgid in catalog.translations['']) {
    if (msgid === '') {
      continue;
    }
    var msg = catalog.translations[''][msgid];
    if (isEmptyMessage(msg)) {
      rv[msgid] = [msgid];
    } else {
      rv[msgid] = msg.msgstr;
    }
  }

  rv[''] = {
    domain: 'messages',
    plural_forms: catalog.headers['plural-forms'],
    lang: catalog.headers['language'],
  };

  return rv;
}

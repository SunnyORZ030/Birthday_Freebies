const fs = require('fs');
const vm = require('vm');

const filePath = 'assets/data/freebies-data.js';
const src = fs.readFileSync(filePath, 'utf8');
const sandbox = { window: {} };
vm.createContext(sandbox);
vm.runInContext(src, sandbox);

const dataByRegion = sandbox.window.BIRTHDAY_FREEBIES_DATA_BY_REGION || {
  bay_area: sandbox.window.BIRTHDAY_FREEBIES_DATA || []
};

const replacements = [
  ['不需要', 'Not required'],
  ['需要', 'Required'],
  ['生日當天', 'Birthday day'],
  ['生日月份', 'Birthday month'],
  ['免費', 'Free'],
  ['任意尺寸', 'Any size'],
  ['任意', 'Any'],
  ['當天', 'same day'],
  ['有效', 'valid'],
  ['天內', 'days'],
  ['前一天', 'day before'],
  ['後一天', 'day after'],
  ['加入', 'join'],
  ['帳號', 'account'],
  ['消費', 'purchase'],
  ['不含', 'excluding'],
  ['實體店', 'in-store'],
  ['線上', 'online'],
  ['門市', 'store location'],
  ['英里', 'miles'],
  ['需', 'must'],
  ['才能', 'to'],
  ['領取', 'redeem'],
  ['條件', 'conditions'],
  ['最寬鬆', 'most flexible'],
  ['以官方通知為準', 'subject to official notice']
];

function pseudoTranslate(text) {
  if (typeof text !== 'string') return text;
  let out = text;
  for (const [from, to] of replacements) {
    out = out.split(from).join(to);
  }
  return out;
}

for (const regionKey of Object.keys(dataByRegion)) {
  dataByRegion[regionKey] = dataByRegion[regionKey].map((entry) => {
    const next = { ...entry };
    delete next.cp;
    delete next.batch;
    delete next.dist;
    for (const field of ['name', 'item', 'member', 'window', 'note']) {
      if (typeof entry[field] === 'string') {
        next[`${field}_en`] = pseudoTranslate(entry[field]);
      }
    }
    return next;
  });
}

const out =
  'window.BIRTHDAY_FREEBIES_DATA_BY_REGION = ' +
  JSON.stringify(dataByRegion, null, 2) +
  ';\n\n' +
  'window.BIRTHDAY_FREEBIES_DATA = window.BIRTHDAY_FREEBIES_DATA_BY_REGION.bay_area;\n';

fs.writeFileSync(filePath, out, 'utf8');
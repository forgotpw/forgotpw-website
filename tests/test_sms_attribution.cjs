const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const script = fs.readFileSync(path.join(__dirname, '../src/scripts/rosa.js'), 'utf8');
function run(search, device = {}) {
  let clicks = 0;
  const links = Array.from({ length: 7 }, () => ({
    href: 'sms:+18647778711', getAttribute() { return this.href; },
    addEventListener(name, callback) { this.click = callback; }
  }));
  vm.runInNewContext(script, {
    document: { querySelector: () => null, getElementById: () => null, querySelectorAll: () => links },
    window: { location: { search, hash: '' }, addEventListener() {} },
    navigator: { userAgent: 'Android', platform: 'Linux', maxTouchPoints: 1, ...device },
    URLSearchParams, HTMLDetailsElement: class {},
    fireConversionScripts() { clicks++; }
  });
  return { links, clicks: () => clicks };
}
const query = '?utm_campaign=rosa_good_dog_oct2026&utm_medium=paid_social';
test('ad links prepare a natural greeting and clicks remain a separate event', () => {
  const result = run(query);
  for (const link of result.links) {
    assert.equal(link.href, 'sms:+18647778711?body=Hi%20Rosa!%20I%20saw%20your%20ad.');
    link.click();
  }
  assert.equal(result.clicks(), 7);
});
test('Apple phone and iPad links use their SMS body delimiter', () => {
  for (const device of [{ userAgent: 'iPhone' }, { userAgent: 'iPad' },
    { userAgent: 'Macintosh', platform: 'MacIntel', maxTouchPoints: 5 }]) {
    assert.equal(run(query, device).links[0].href,
      'sms:+18647778711&body=Hi%20Rosa!%20I%20saw%20your%20ad.');
  }
});
test('organic, unknown and non-ad campaigns preserve plain SMS links', () => {
  for (const search of ['', '?utm_campaign=rosa_good_dog_oct2026',
    '?utm_campaign=other&utm_medium=paid_social',
    '?utm_campaign=rosa_good_dog_oct2026&utm_medium=email']) {
    assert.equal(run(search).links[0].href, 'sms:+18647778711');
  }
});

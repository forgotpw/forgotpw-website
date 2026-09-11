const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');

const template = fs.readFileSync(path.join(__dirname,
  '../terraform/apex-redirect/redirect.js.tftpl'), 'utf8');

for (const host of ['www-dev.rosa.bot', 'www.rosa.bot']) {
  const context = vm.createContext({});
  vm.runInContext(template.replace('${canonical_hostname}', host), context);
  test(`${host}: permanent HTTPS redirect preserves path and encoded duplicate parameters`, () => {
    const response = context.handler({ request: {
      uri: '/privacy.html',
      headers: { host: { value: 'untrusted.example' } },
      querystring: {
        utm_source: { value: 'email%20campaign' },
        tag: { value: 'a', multiValue: [{ value: 'a' }, { value: 'b%26c' }] },
        empty: { value: '' },
      },
    } });
    assert.equal(response.statusCode, 301);
    assert.equal(response.headers.location.value,
      `https://${host}/privacy.html?utm_source=email%20campaign&tag=a&tag=b%26c&empty=`);
  });
  test(`${host}: root has no trailing question mark and does not trust request host`, () => {
    const response = context.handler({ request: { uri: '/', querystring: {} } });
    assert.equal(response.headers.location.value, `https://${host}/`);
  });
}

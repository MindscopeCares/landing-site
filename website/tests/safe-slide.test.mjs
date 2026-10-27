import { test } from 'node:test';
import assert from 'node:assert/strict';
import { JSDOM } from 'jsdom';
const dom = new JSDOM('');
globalThis.window = dom.window;
const { safeSlideDocument } = await import('../.test-build/safeSlide.js');

test('AI markup cannot create scripts, events, external resources, or navigation', () => {
  const result = new JSDOM(safeSlideDocument(`<script>parent.location='https://evil.invalid'</script><div onclick="alert(1)">Evidence</div><img src="https://evil.invalid/collect"><iframe srcdoc="<script>alert(1)</script>"></iframe><form action="https://evil.invalid"><input name=x></form><a href="javascript:alert(1)">Read</a>`));
  const doc = result.window.document;
  assert.equal(doc.querySelector('script,iframe,img,form,input,a'), null);
  assert.equal(doc.querySelector('[onclick]'), null);
  assert.match(doc.body.textContent, /Evidence/);
  assert.match(doc.querySelector('meta').content, /default-src 'none'/);
});
test('ordinary headings and list content survive sanitization', () => {
  const result = new JSDOM(safeSlideDocument('<h1>Reading support</h1><ul><li>Review classroom evidence</li></ul>'));
  assert.equal(result.window.document.querySelector('h1').textContent, 'Reading support');
  assert.equal(result.window.document.querySelector('li').textContent, 'Review classroom evidence');
});
test('oversized slide output is rejected before rendering', () => {
  assert.throws(() => safeSlideDocument('a'.repeat(100001)), /too large/);
});

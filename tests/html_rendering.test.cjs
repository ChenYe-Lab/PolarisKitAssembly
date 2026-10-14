const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { escapeHtml } = require('../KitAssembly/kitapp/kitserver/static/js/html.js');

test('external values cannot create HTML elements or close quoted attributes', () => {
    const attack = '\"><img src=x onerror=alert(1)>&\'';
    assert.equal(escapeHtml(attack), '&quot;&gt;&lt;img src=x onerror=alert(1)&gt;&amp;&#39;');
    assert.equal(escapeHtml(null), '');
});

test('actual card renderer escapes every external field', () => {
    const template = fs.readFileSync(path.join(__dirname, '../KitAssembly/kitapp/kitserver/templates/index.html'), 'utf8');
    const start = template.indexOf('        function renderCards()');
    const end = template.indexOf('\n        function ', start + 20);
    assert.ok(start > 0 && end > start);
    const malicious = '\"><img src=x onerror=alert(1)>';
    const cards = [];
    const context = {
        escapeHtml, cardsGrid: { appendChild: card => cards.push(card) },
        libraryTag: {}, cardsSummary: {}, currentCategory: 'test', currentType: 'part',
        selectedComponents: [], t: key => key, componentKey: name => name,
        normalizeText: value => String(value),
        getCurrentList: () => [{status:true, name:malicious, type:malicious, part:malicious,
            length:malicious, marker:malicious, ori:malicious, user:malicious,
            scar:{bbsi:malicious, bsai:malicious}}],
        document: {createElement: () => ({}), querySelectorAll: () => []},
    };
    vm.runInNewContext(template.slice(start, end) + '\nrenderCards();', context);
    assert.equal(cards.length, 1);
    assert.ok(!cards[0].innerHTML.toLowerCase().includes('<img'));
    assert.ok(cards[0].innerHTML.includes('data-id="' + escapeHtml(malicious) + '"'));
});

// harakat.js
// Safely wrap Arabic diacritics (harakat) in a span.haraka inside verse display nodes.
// Idempotent: marks processed containers with data-harakat-processed="1".

(function(window, document){
    'use strict';

    // Unicode ranges: 064B-0652 covers most Arabic diacritics; include 0670 and 0651 explicitly
    const HARAKAT_RE = /[\u064B-\u0652\u0670\u0651]/g;

    function hasAncestorWithClass(node, className) {
        let el = node.parentElement;
        while (el) {
            if (el.classList && el.classList.contains(className)) return true;
            el = el.parentElement;
        }
        return false;
    }

    function shouldSkip(node) {
        if (!node.parentNode) return true;
        // skip inside already-processed haraka spans
        if (hasAncestorWithClass(node, 'haraka')) return true;
        // skip inside script/style
        let el = node.parentElement;
        while (el) {
            const tag = el.tagName;
            if (!tag) break;
            if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'NOSCRIPT' || tag === 'CODE' || tag === 'PRE') return true;
            el = el.parentElement;
        }
        return false;
    }

    function processTextNode(node) {
        const text = node.nodeValue;
        if (!text) return;
        HARAKAT_RE.lastIndex = 0;
        if (!HARAKAT_RE.test(text)) return; // no harakat

        // rebuild fragment with harakat wrapped
        HARAKAT_RE.lastIndex = 0;
        let lastIndex = 0;
        let match;
        const frag = document.createDocumentFragment();
        while ((match = HARAKAT_RE.exec(text)) !== null) {
            const idx = match.index;
            if (idx > lastIndex) {
                frag.appendChild(document.createTextNode(text.slice(lastIndex, idx)));
            }
            const span = document.createElement('span');
            span.className = 'haraka';
            span.textContent = match[0];
            frag.appendChild(span);
            lastIndex = HARAKAT_RE.lastIndex;
        }
        if (lastIndex < text.length) {
            frag.appendChild(document.createTextNode(text.slice(lastIndex)));
        }
        node.parentNode.replaceChild(frag, node);
    }

    function traverseAndProcess(root) {
        // TreeWalker to visit text nodes only
        const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null, false);
        const nodes = [];
        let node;
        while ((node = walker.nextNode())) {
            nodes.push(node);
        }
        for (let i = 0; i < nodes.length; i++) {
            const t = nodes[i];
            if (shouldSkip(t)) continue;
            processTextNode(t);
        }
    }

    function colorizeElement(el) {
        if (!el) return;
        if (el.dataset && el.dataset.harakatProcessed === '1') return;
        traverseAndProcess(el);
        if (el.dataset) el.dataset.harakatProcessed = '1';
    }

    function init(selector) {
        // default selector targets verse display nodes
        const sel = selector || '.verses-container, .verse, .verse-text';
        const elements = document.querySelectorAll(sel);
        elements.forEach(el => colorizeElement(el));
    }

    // expose
    window.HarakatColorize = {
        init: init,
        colorizeElement: colorizeElement
    };

})(window, document);

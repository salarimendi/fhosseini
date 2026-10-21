
/*

(function(window, document){
'use strict';

const map = {
 '\u064E': 'fatha',
 '\u064F': 'damma',
 '\u0650': 'kasra',
 '\u0651': 'tashdid',
 '\u0652': 'sukun',
 '\u064B': 'fathatan',
 '\u064C': 'dammatan',
 '\u064D': 'kasratan'
};

const HARAKAT = '\u064B-\u0652';

function colorizeElement(el){

 if (el.dataset.harakatProcessed === '1') return;

 el.innerHTML = el.innerHTML.replace(
   new RegExp(`([\\u0621-\\u064A])([${HARAKAT}]+)`, 'g'),
   (m, letter, marks) => {
       const cls = map[marks[0]] || 'haraka';
       return `<span class="${cls}">${letter}${marks}</span>`;
   }
 );

 el.dataset.harakatProcessed = '1';
}

function init(selector){
 const sel = selector || '.verses-container, .verse, .verse-text';
 document.querySelectorAll(sel).forEach(colorizeElement);
}

window.HarakatColorize = { init };

})(window, document);

document.addEventListener("DOMContentLoaded", () => {
 if (window.HarakatColorize) HarakatColorize.init();
});
*/

// harakat.js
// Simple diacritic coloring and positioning - exactly as shown in reference.
// Wraps each diacritic in a span with appropriate class name.
// Idempotent: marks processed containers with data-harakat-processed="1".

(function(window, document){
    'use strict';

    // Map Unicode to class names
    const map = {
        '\u064E': 'fatha',      // فتحة
        '\u064F': 'damma',      // ضمة
        '\u0650': 'kasra',      // كسرة
        '\u0651': 'tashdid',    // تشديد
        '\u0652': 'sukun',      // سكون
        '\u064B': 'fathatan',   // فتحتان
        '\u064C': 'dammatan',   // ضمتان
        '\u064D': 'kasratan'    // كسرتان
    };

    function colorizeElement(element) {
        // Skip if already processed
        if (element.dataset && element.dataset.harakatProcessed === '1') {
            return;
        }

        // Simple replace on innerHTML
        element.innerHTML = element.innerHTML.replace(/[\u064B-\u0652]/g, ch => {
            const cls = map[ch] || 'haraka';
            return `<span class="${cls}">${ch}</span>`;
        });

        if (element.dataset) {
            element.dataset.harakatProcessed = '1';
        }
    }

    function init(selector) {
        const sel = selector || '.verses-container, .verse, .verse-text';
        const elements = document.querySelectorAll(sel);
        elements.forEach(el => colorizeElement(el));
    }

    window.HarakatColorize = {
        init: init,
        colorizeElement: colorizeElement
    };

})(window, document);
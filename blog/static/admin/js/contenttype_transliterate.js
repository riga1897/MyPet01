(function() {
    'use strict';

    const CYRILLIC_MAP = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    };

    function transliterate(text) {
        let result = '';
        for (let char of text.toLowerCase()) {
            if (CYRILLIC_MAP[char] !== undefined) {
                result += CYRILLIC_MAP[char];
            } else if (/[a-z0-9_-]/.test(char)) {
                result += char;
            } else if (char === ' ' || char === '\t') {
                result += '_';
            }
        }
        return result;
    }

    document.addEventListener('DOMContentLoaded', function() {
        const nameField = document.getElementById('id_name');
        const codeField = document.getElementById('id_code');

        if (!nameField || !codeField) return;

        let userEditedCode = codeField.value !== '';

        nameField.addEventListener('input', function() {
            if (!userEditedCode) {
                codeField.value = transliterate(nameField.value);
            }
        });

        codeField.addEventListener('input', function() {
            userEditedCode = codeField.value !== '';
        });
    });
})();

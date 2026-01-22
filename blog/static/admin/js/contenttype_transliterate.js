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

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    function showMessage(field, message, isError) {
        let msgEl = field.nextElementSibling;
        if (!msgEl || !msgEl.classList.contains('code-status')) {
            msgEl = document.createElement('span');
            msgEl.classList.add('code-status');
            msgEl.style.marginLeft = '10px';
            msgEl.style.fontSize = '11px';
            field.parentNode.insertBefore(msgEl, field.nextSibling);
        }
        msgEl.textContent = message;
        msgEl.style.color = isError ? '#e74c3c' : '#27ae60';
    }

    function clearMessage(field) {
        const msgEl = field.nextElementSibling;
        if (msgEl && msgEl.classList.contains('code-status')) {
            msgEl.textContent = '';
        }
    }

    async function checkCodeUniqueness(code, excludeId) {
        if (!code) return { available: true };
        
        const params = new URLSearchParams({ code });
        if (excludeId) params.append('exclude_id', excludeId);
        
        try {
            const response = await fetch(`/api/check-contenttype-code/?${params}`);
            return await response.json();
        } catch (e) {
            console.error('Error checking code:', e);
            return { available: true };
        }
    }

    document.addEventListener('DOMContentLoaded', function() {
        const nameField = document.getElementById('id_name');
        const codeField = document.getElementById('id_code');
        const folderField = document.getElementById('id_upload_folder');

        if (!nameField || !codeField) return;

        const url = window.location.pathname;
        const match = url.match(/\/contenttype\/(\d+)\/change\//);
        const excludeId = match ? match[1] : null;

        let userEditedCode = codeField.value !== '';
        let userEditedFolder = folderField && folderField.value !== '' && folderField.value !== codeField.value;

        function updateCode(newCode) {
            codeField.value = newCode;
            if (folderField && !userEditedFolder) {
                folderField.value = newCode;
            }
        }

        const debouncedCheck = debounce(async function(code) {
            if (!code) {
                clearMessage(codeField);
                return;
            }
            
            const result = await checkCodeUniqueness(code, excludeId);
            
            if (!result.available) {
                showMessage(codeField, `Код занят. Предлагается: ${result.suggested}`, true);
            } else {
                showMessage(codeField, '✓ Код доступен', false);
            }
        }, 300);

        nameField.addEventListener('input', function() {
            if (!userEditedCode) {
                const newCode = transliterate(nameField.value);
                updateCode(newCode);
                debouncedCheck(newCode);
            }
        });

        codeField.addEventListener('input', function() {
            userEditedCode = codeField.value !== '';
            if (folderField && !userEditedFolder) {
                folderField.value = codeField.value;
            }
            debouncedCheck(codeField.value);
        });

        if (folderField) {
            folderField.addEventListener('input', function() {
                userEditedFolder = folderField.value !== '' && folderField.value !== codeField.value;
            });
        }

        if (codeField.value) {
            debouncedCheck(codeField.value);
        }
    });
})();

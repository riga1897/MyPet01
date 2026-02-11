"""Text utilities for keyboard layout conversion and transliteration."""

from typing import Literal

QWERTY_TO_CYRILLIC: dict[str, str] = {
    'q': 'й', 'w': 'ц', 'e': 'у', 'r': 'к', 't': 'е', 'y': 'н', 'u': 'г',
    'i': 'ш', 'o': 'щ', 'p': 'з', '[': 'х', ']': 'ъ', 'a': 'ф', 's': 'ы',
    'd': 'в', 'f': 'а', 'g': 'п', 'h': 'р', 'j': 'о', 'k': 'л', 'l': 'д',
    ';': 'ж', "'": 'э', 'z': 'я', 'x': 'ч', 'c': 'с', 'v': 'м', 'b': 'и',
    'n': 'т', 'm': 'ь', ',': 'б', '.': 'ю', '/': '.', '`': 'ё',
    'Q': 'Й', 'W': 'Ц', 'E': 'У', 'R': 'К', 'T': 'Е', 'Y': 'Н', 'U': 'Г',
    'I': 'Ш', 'O': 'Щ', 'P': 'З', '{': 'Х', '}': 'Ъ', 'A': 'Ф', 'S': 'Ы',
    'D': 'В', 'F': 'А', 'G': 'П', 'H': 'Р', 'J': 'О', 'K': 'Л', 'L': 'Д',
    ':': 'Ж', '"': 'Э', 'Z': 'Я', 'X': 'Ч', 'C': 'С', 'V': 'М', 'B': 'И',
    'N': 'Т', 'M': 'Ь', '<': 'Б', '>': 'Ю', '?': ',', '~': 'Ё',
}

CYRILLIC_TO_QWERTY: dict[str, str] = {v: k for k, v in QWERTY_TO_CYRILLIC.items()}

CYRILLIC_TRANSLIT: dict[str, str] = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
}


def is_latin(text: str) -> bool:
    """Check if text contains mostly Latin characters."""
    if not text:
        return False
    latin_count = sum(1 for c in text if c.isalpha() and ord(c) < 256)
    cyrillic_count = sum(1 for c in text if c.isalpha() and ord(c) >= 0x0400 and ord(c) <= 0x04FF)
    return latin_count > cyrillic_count


def is_cyrillic(text: str) -> bool:
    """Check if text contains mostly Cyrillic characters."""
    if not text:
        return False
    return not is_latin(text)


def convert_layout(
    text: str,
    direction: Literal['en_to_ru', 'ru_to_en', 'auto'] = 'auto'
) -> str:
    """Convert text between keyboard layouts (QWERTY ↔ ЙЦУКЕН).

    Args:
        text: Input text to convert.
        direction: Conversion direction:
            - 'en_to_ru': Convert Latin to Cyrillic (QWERTY → ЙЦУКЕН)
            - 'ru_to_en': Convert Cyrillic to Latin (ЙЦУКЕН → QWERTY)
            - 'auto': Auto-detect based on text content

    Returns:
        Converted text with keyboard layout changed.

    Example:
        >>> convert_layout('ntcn')  # User typed "тест" with EN layout
        'тест'
        >>> convert_layout('еуче', 'ru_to_en')
        'text'
    """
    if not text:
        return text

    if direction == 'auto':
        direction = 'en_to_ru' if is_latin(text) else 'ru_to_en'

    mapping = QWERTY_TO_CYRILLIC if direction == 'en_to_ru' else CYRILLIC_TO_QWERTY

    result = []
    for char in text:
        result.append(mapping.get(char, char))

    return ''.join(result)


def transliterate(text: str) -> str:
    """Transliterate Cyrillic text to Latin (for slugs/codes).

    Args:
        text: Cyrillic text to transliterate.

    Returns:
        Latin transliteration of the text.

    Example:
        >>> transliterate('Привет мир')
        'privet_mir'
    """
    if not text:
        return ''

    result = []
    for char in text:
        if char in CYRILLIC_TRANSLIT:
            result.append(CYRILLIC_TRANSLIT[char])
        elif char.isalnum() or char in '-_':
            result.append(char.lower())
        elif char in ' \t':
            result.append('_')

    return ''.join(result)

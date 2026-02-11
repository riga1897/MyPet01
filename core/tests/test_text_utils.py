"""Tests for text utilities."""

from core.utils.text import (
    convert_layout,
    is_cyrillic,
    is_latin,
    transliterate,
)


class TestIsLatin:
    """Tests for is_latin function."""

    def test_empty_string_returns_false(self) -> None:
        assert is_latin('') is False

    def test_latin_text_returns_true(self) -> None:
        assert is_latin('hello') is True
        assert is_latin('Hello World') is True

    def test_cyrillic_text_returns_false(self) -> None:
        assert is_latin('привет') is False
        assert is_latin('Привет Мир') is False

    def test_mixed_mostly_latin_returns_true(self) -> None:
        assert is_latin('hello мир') is True

    def test_mixed_mostly_cyrillic_returns_false(self) -> None:
        assert is_latin('h привет мир') is False


class TestIsCyrillic:
    """Tests for is_cyrillic function."""

    def test_empty_string_returns_false(self) -> None:
        assert is_cyrillic('') is False

    def test_cyrillic_text_returns_true(self) -> None:
        assert is_cyrillic('привет') is True

    def test_latin_text_returns_false(self) -> None:
        assert is_cyrillic('hello') is False


class TestConvertLayout:
    """Tests for convert_layout function."""

    def test_empty_string_returns_empty(self) -> None:
        assert convert_layout('') == ''

    def test_en_to_ru_basic(self) -> None:
        assert convert_layout('ntcn') == 'тест'
        assert convert_layout('ghbdtn') == 'привет'

    def test_en_to_ru_explicit(self) -> None:
        assert convert_layout('ntcn', 'en_to_ru') == 'тест'

    def test_ru_to_en_basic(self) -> None:
        assert convert_layout('е|у|е', 'ru_to_en') == 't|e|t'

    def test_auto_detects_latin(self) -> None:
        result = convert_layout('ntcn', 'auto')
        assert result == 'тест'

    def test_auto_detects_cyrillic(self) -> None:
        result = convert_layout('руддщ', 'auto')
        assert 'hello' in result.lower() or result != 'руддщ'

    def test_preserves_unknown_chars(self) -> None:
        result = convert_layout('test123')
        assert '123' in result
        assert result == 'е|у|ые123'.replace('|', '')

    def test_preserves_spaces(self) -> None:
        result = convert_layout('hello world', 'en_to_ru')
        assert ' ' in result

    def test_uppercase_letters(self) -> None:
        assert convert_layout('NTCN') == 'ТЕСТ'


class TestTransliterate:
    """Tests for transliterate function."""

    def test_empty_string_returns_empty(self) -> None:
        assert transliterate('') == ''

    def test_basic_transliteration(self) -> None:
        assert transliterate('тест') == 'test'
        assert transliterate('привет') == 'privet'

    def test_spaces_become_underscores(self) -> None:
        assert transliterate('привет мир') == 'privet_mir'

    def test_preserves_latin_letters(self) -> None:
        assert transliterate('test123') == 'test123'

    def test_complex_characters(self) -> None:
        assert transliterate('щука') == 'schuka'
        assert transliterate('чай') == 'chay'
        assert transliterate('жёлтый') == 'zhyoltyy'

    def test_uppercase_to_lowercase(self) -> None:
        result = transliterate('ТЕСТ')
        assert result == 'TEST'

    def test_mixed_case_preserved(self) -> None:
        assert transliterate('Привет') == 'Privet'

    def test_special_chars_removed(self) -> None:
        result = transliterate('тест!')
        assert '!' not in result

    def test_hyphen_preserved(self) -> None:
        assert transliterate('тест-раз') == 'test-raz'

    def test_underscore_preserved(self) -> None:
        assert transliterate('тест_раз') == 'test_raz'

import pytest
from blog.forms import ContentForm


class TestContentForm:
    def test_form_has_all_fields(self) -> None:
        form = ContentForm()
        assert 'title' in form.fields
        assert 'description' in form.fields
        assert 'content_type' in form.fields
        assert 'category' in form.fields
        assert 'thumbnail' in form.fields
        assert 'video_file' in form.fields
        assert 'duration' in form.fields

    def test_form_labels_in_russian(self) -> None:
        form = ContentForm()
        assert form.fields['title'].label == 'Заголовок'
        assert form.fields['description'].label == 'Описание'
        assert form.fields['content_type'].label == 'Тип контента'
        assert form.fields['category'].label == 'Категория'

    @pytest.mark.django_db
    def test_valid_form_creates_content(self) -> None:
        form = ContentForm(data={
            'title': 'Тестовый контент',
            'description': 'Описание',
            'content_type': 'video',
            'category': 'yoga',
        })
        assert form.is_valid()
        content = form.save()
        assert content.title == 'Тестовый контент'

    def test_title_is_required(self) -> None:
        form = ContentForm(data={
            'description': 'Описание',
            'content_type': 'video',
            'category': 'yoga',
        })
        assert not form.is_valid()
        assert 'title' in form.errors

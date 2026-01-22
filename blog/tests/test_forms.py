import pytest
from blog.forms import ContentForm
from blog.models import Category, ContentType


class TestContentForm:
    def test_form_has_all_fields(self) -> None:
        form = ContentForm()
        assert 'title' in form.fields
        assert 'description' in form.fields
        assert 'content_type' in form.fields
        assert 'category' in form.fields
        assert 'thumbnail' in form.fields
        assert 'video_file' in form.fields

    def test_form_labels_in_russian(self) -> None:
        form = ContentForm()
        assert form.fields['title'].label == 'Заголовок'
        assert form.fields['description'].label == 'Описание'
        assert form.fields['content_type'].label == 'Тип контента'
        assert form.fields['category'].label == 'Категория'

    @pytest.mark.django_db
    def test_valid_form_creates_content(self, yoga_category: Category, video_type: ContentType) -> None:
        form = ContentForm(data={
            'title': 'Тестовый контент',
            'description': 'Описание',
            'content_type': video_type.pk,
            'category': yoga_category.pk,
        })
        assert form.is_valid(), form.errors
        content = form.save()
        assert content.title == 'Тестовый контент'
        assert content.content_type == video_type

    @pytest.mark.django_db
    def test_valid_form_without_content_type(self, yoga_category: Category) -> None:
        form = ContentForm(data={
            'title': 'Контент без типа',
            'description': 'Описание',
            'category': yoga_category.pk,
        })
        assert form.is_valid(), form.errors
        content = form.save()
        assert content.content_type is None

    def test_title_is_required(self) -> None:
        form = ContentForm(data={
            'description': 'Описание',
        })
        assert not form.is_valid()
        assert 'title' in form.errors

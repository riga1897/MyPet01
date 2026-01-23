import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from blog.forms import ContentForm
from blog.models import Category, ContentType


class TestContentForm:
    def test_form_has_all_fields(self) -> None:
        form = ContentForm()
        assert 'title' in form.fields
        assert 'description' in form.fields
        assert 'content_type' in form.fields
        assert 'categories' in form.fields
        assert 'thumbnail' in form.fields
        assert 'video_file' in form.fields

    def test_form_labels_in_russian(self) -> None:
        form = ContentForm()
        assert form.fields['title'].label == 'Заголовок'
        assert form.fields['description'].label == 'Описание'
        assert form.fields['content_type'].label == 'Тип контента'
        assert form.fields['categories'].label == 'Категории'

    @pytest.mark.django_db
    def test_valid_form_creates_content(self, yoga_category: Category, video_type: ContentType) -> None:
        form = ContentForm(data={
            'title': 'Тестовый контент',
            'description': 'Описание',
            'content_type': video_type.pk,
            'categories': [yoga_category.pk],
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
            'categories': [yoga_category.pk],
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

    @pytest.mark.django_db
    def test_save_adds_hash_to_uploaded_file(
        self, yoga_category: Category, video_type: ContentType
    ) -> None:
        """When saving with uploaded file, filename should get MD5 hash."""
        file_content = b'test video content for hashing'
        uploaded_file = SimpleUploadedFile('my_video.mp4', file_content)
        
        from django.utils.datastructures import MultiValueDict
        form = ContentForm(
            data={
                'title': 'Видео с хэшем',
                'description': 'Тест',
                'content_type': video_type.pk,
                'categories': [yoga_category.pk],
            },
            files=MultiValueDict({'video_file': [uploaded_file]})
        )
        assert form.is_valid(), form.errors
        content = form.save()
        
        assert content.video_file.name is not None
        filename = content.video_file.name.split('/')[-1]
        assert filename.startswith('my_video_')
        assert filename.endswith('.mp4')
        assert len(filename) > len('my_video_.mp4')

    @pytest.mark.django_db
    def test_save_without_file_works(self, yoga_category: Category) -> None:
        """Saving without file should work normally."""
        form = ContentForm(data={
            'title': 'Контент без файла',
            'description': 'Описание',
            'categories': [yoga_category.pk],
        })
        assert form.is_valid(), form.errors
        content = form.save()
        
        assert content.pk is not None
        assert content.title == 'Контент без файла'
        assert not content.video_file

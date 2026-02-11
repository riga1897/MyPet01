import pytest
from blog.models import Content


@pytest.mark.django_db
class TestBaseModel:
    def test_created_at_is_set_automatically(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.created_at is not None

    def test_updated_at_is_set_automatically(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.updated_at is not None

    def test_updated_at_changes_on_save(self) -> None:
        content = Content.objects.create(title='Тест')
        original_updated_at = content.updated_at
        content.title = 'Обновлённый тест'
        content.save()
        content.refresh_from_db()
        assert content.updated_at > original_updated_at

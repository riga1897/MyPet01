import pytest
from blog.models import Category, Content, ContentType, Tag, TagGroup


@pytest.mark.django_db
class TestContentModel:
    def test_content_str_returns_title(self, yoga_category: Category, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Утренняя йога',
            category=yoga_category,
            content_type=video_type,
        )
        assert str(content) == 'Утренняя йога'

    def test_content_default_category_is_none(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.category is None

    def test_content_default_type_is_none(self) -> None:
        content = Content.objects.create(title='Тест')
        assert content.content_type is None

    def test_content_ordering_by_created_at_desc(self, video_type: ContentType) -> None:
        c1 = Content.objects.create(title='Первое', content_type=video_type)
        c2 = Content.objects.create(title='Второе', content_type=video_type)
        contents = list(Content.objects.all())
        assert contents[0] == c2
        assert contents[1] == c1

    def test_content_can_be_video(self, yoga_category: Category, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Видео йоги',
            category=yoga_category,
            content_type=video_type,
        )
        assert content.content_type is not None
        assert content.content_type.is_video is True

    def test_content_can_be_photo(self, yoga_category: Category, photo_type: ContentType) -> None:
        content = Content.objects.create(
            title='Фото йоги',
            category=yoga_category,
            content_type=photo_type,
        )
        assert content.content_type is not None
        assert content.content_type.is_photo is True

    def test_create_content_video(self, video_type: ContentType) -> None:
        content = Content.objects.create(
            title='Мое видео',
            description='Test Video',
            content_type=video_type,
        )
        assert content.description == 'Test Video'
        assert content.content_type is not None
        assert content.content_type.code == 'video'
        assert str(content) == 'Мое видео'

    def test_create_content_photo(self, photo_type: ContentType) -> None:
        content = Content.objects.create(
            title='Моя фотография',
            description='Test Photo',
            content_type=photo_type,
        )
        assert content.description == 'Test Photo'
        assert content.content_type is not None
        assert content.content_type.code == 'photo'
        assert str(content) == 'Моя фотография'


@pytest.mark.django_db
class TestCategoryModel:
    def test_category_str_returns_name(self) -> None:
        category = Category.objects.create(
            name='Тестовая категория',
            code='test',
        )
        assert str(category) == 'Тестовая категория'

    def test_category_code_is_unique(self) -> None:
        Category.objects.create(name='Категория 1', code='cat1')
        with pytest.raises(Exception):
            Category.objects.create(name='Категория 2', code='cat1')


@pytest.mark.django_db
class TestTagGroupModel:
    def test_taggroup_str_returns_name(self) -> None:
        group = TagGroup.objects.create(name='Тестовая группа')
        assert str(group) == 'Тестовая группа'

    def test_taggroup_slug_auto_generated(self) -> None:
        group = TagGroup.objects.create(name='Месяц практики')
        assert group.slug == 'месяц-практики'

    def test_taggroup_is_visible_for_category_when_empty(self, yoga_category: Category) -> None:
        group = TagGroup.objects.create(name='Универсальная группа')
        assert group.is_visible_for_category(yoga_category) is True

    def test_taggroup_is_visible_for_category_when_linked(
        self, yoga_category: Category, oils_category: Category
    ) -> None:
        group = TagGroup.objects.create(name='Только йога')
        group.categories.add(yoga_category)
        assert group.is_visible_for_category(yoga_category) is True
        assert group.is_visible_for_category(oils_category) is False

    def test_taggroup_is_visible_for_category_none(self) -> None:
        group = TagGroup.objects.create(name='Группа тест')
        assert group.is_visible_for_category(None) is True
        group.categories.add(Category.objects.create(name='Cat тест', code='cat_test'))
        assert group.is_visible_for_category(None) is False


@pytest.mark.django_db
class TestTagModel:
    def test_tag_str_returns_group_and_name(self) -> None:
        group = TagGroup.objects.create(name='Месяц')
        tag = Tag.objects.create(name='Первый', group=group)
        assert str(tag) == 'Месяц: Первый'

    def test_tag_slug_auto_generated(self) -> None:
        group = TagGroup.objects.create(name='Группа')
        tag = Tag.objects.create(name='Расслабление', group=group)
        assert tag.slug == 'расслабление'

    def test_tag_ordering(self) -> None:
        group = TagGroup.objects.create(name='Группа')
        t1 = Tag.objects.create(name='Второй', group=group, order=2)
        t2 = Tag.objects.create(name='Первый', group=group, order=1)
        tags = list(Tag.objects.all())
        assert tags[0] == t2
        assert tags[1] == t1


@pytest.mark.django_db
class TestContentTypeModel:
    def test_contenttype_str_returns_name(self, video_type: ContentType) -> None:
        assert str(video_type) == 'Видео'

    def test_contenttype_is_video_property(self, video_type: ContentType) -> None:
        assert video_type.is_video is True
        assert video_type.is_photo is False

    def test_contenttype_is_photo_property(self, photo_type: ContentType) -> None:
        assert photo_type.is_photo is True
        assert photo_type.is_video is False

    def test_contenttype_code_is_required(self) -> None:
        ct = ContentType(name='Без кода тест')
        with pytest.raises(Exception):
            ct.full_clean()

    def test_contenttype_code_is_unique(self) -> None:
        ContentType.objects.create(name='Уникальный тип 1', code='unique_type1')
        with pytest.raises(Exception):
            ContentType.objects.create(name='Уникальный тип 2', code='unique_type1')

    def test_contenttype_upload_folder_defaults_to_code(self) -> None:
        ct = ContentType.objects.create(name='Аудио тест', code='audio_test')
        assert ct.upload_folder == 'audio_test'

    def test_contenttype_upload_folder_custom(self) -> None:
        ct = ContentType.objects.create(name='Документы тест', code='docs_test', upload_folder='documents')
        assert ct.upload_folder == 'documents'

    def test_contenttype_has_related_content_false_when_empty(self) -> None:
        ct = ContentType.objects.create(name='Пустой тип', code='empty_type')
        assert ct.has_related_content() is False
        assert ct.get_related_content_count() == 0

    def test_contenttype_has_related_content_true_when_content_exists(
        self, video_type: ContentType
    ) -> None:
        Content.objects.create(title='Тест', content_type=video_type)
        assert video_type.has_related_content() is True
        assert video_type.get_related_content_count() == 1

    def test_contenttype_delete_without_content_succeeds(self) -> None:
        ct = ContentType.objects.create(name='Удаляемый', code='deletable')
        ct_id = ct.id
        ct.delete()
        assert not ContentType.objects.filter(id=ct_id).exists()

    def test_contenttype_delete_with_content_raises_error(
        self, video_type: ContentType
    ) -> None:
        Content.objects.create(title='Тест', content_type=video_type)
        with pytest.raises(ValueError, match='Невозможно удалить'):
            video_type.delete()
